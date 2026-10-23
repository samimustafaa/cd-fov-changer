"""Signed-checksum verified GitHub Release updater for the portable Windows build."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path
from tkinter import messagebox

VERSION = "0.1.0"
REPO = "samimustafaa/cd-fov-changer"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
ASSET = "sg0hann-FOV-Changer.exe"
HEADERS = {"Accept":"application/vnd.github+json","User-Agent":f"sg0hann-FOV-Changer/{VERSION}"}

def version_parts(v):
    return tuple(int(n) for n in v.lstrip("v").split(".") if n.isdigit())

def get_bytes(url, maximum=100_000_000):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=18) as response:
        data=response.read(maximum+1)
    if len(data)>maximum:raise RuntimeError("Update file too large")
    return data

def check_for_updates(window, manual=False):
    def notify(message):
        window.after(0,lambda: messagebox.showinfo("FOV Changer Updates",message))
    def work():
        try:
            release=json.loads(get_bytes(API,2_000_000))
            latest=release["tag_name"]
            if version_parts(latest)<=version_parts(VERSION):
                if manual:notify("You already have the latest version.")
                return
            exe=next((x for x in release.get("assets",[]) if x["name"]==ASSET),None)
            sums=next((x for x in release.get("assets",[]) if x["name"]=="SHA256SUMS.txt"),None)
            if not exe or not sums:
                notify("An update exists, but its verified Windows package is not available yet.\n"+release["html_url"])
                return
            def offer():
                if messagebox.askyesno("Update available",f"Version {latest} is available.\nDownload, verify and install it now?"):
                    threading.Thread(target=lambda:install(exe,sums,window),daemon=True).start()
            window.after(0,offer)
        except Exception as e:
            if manual:notify("Could not check GitHub Releases:\n"+str(e))
    threading.Thread(target=work,daemon=True).start()

def install(exe,sums,window):
    def error(msg):
        window.after(0,lambda:messagebox.showerror("Update failed",msg))
    try:
        if not getattr(sys,"frozen",False):
            error("Automatic replacement is available in the packaged Windows .exe only.")
            return
        expected=None
        for line in get_bytes(sums["browser_download_url"],100_000).decode("utf-8").splitlines():
            parts=line.strip().split()
            if len(parts)==2 and parts[1].lstrip("*")==ASSET:
                expected=parts[0].lower()
        if not expected or len(expected)!=64:
            raise RuntimeError("Missing SHA-256 checksum for executable")
        payload=get_bytes(exe["browser_download_url"])
        actual=hashlib.sha256(payload).hexdigest()
        if actual!=expected:raise RuntimeError("SHA-256 mismatch. Update discarded.")
        current=Path(sys.executable).resolve()
        folder=Path(tempfile.mkdtemp(prefix="sg0hann-update-"))
        staged=folder/ASSET
        staged.write_bytes(payload)
        # Windows cannot overwrite a running exe. An external PowerShell process
        # waits until this PID exits, then swaps the executable and relaunches it.
        script=folder/"apply.ps1"
        script.write_text(
            "param([int]$OldPid,[string]$Source,[string]$Target)\n"
            "try { Wait-Process -Id $OldPid -ErrorAction SilentlyContinue } catch {}\n"
            "Start-Sleep -Milliseconds 700\n"
            "Copy-Item -LiteralPath $Source -Destination $Target -Force -ErrorAction Stop\n"
            "Start-Process -FilePath $Target\n"
            ,encoding="utf-8")
        flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
        subprocess.Popen(["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass",
            "-File",str(script),"-OldPid",str(os.getpid()),"-Source",str(staged),
            "-Target",str(current)],creationflags=flags,close_fds=True)
        window.after(0,window.destroy)
    except Exception as e:error(str(e))
