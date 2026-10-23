"""GitHub Releases updater for a portable, folder-based Windows app."""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path
from tkinter import messagebox

VERSION = "0.3.1"
REPO = "samimustafaa/cd-fov-changer"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
ASSET = "sg0hann-FOV-Changer-win64.zip"
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": f"sg0hann-FOV-Changer/{VERSION}"}

def version_parts(v):
    return tuple(int(n) for n in v.lstrip("v").split(".") if n.isdigit())

def get_bytes(url, maximum=180_000_000):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=50) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise RuntimeError("Download exceeded size limit.")
    return data

def check_for_updates(window, manual=False):
    def notify(message):
        window.after(0, lambda: messagebox.showinfo("FOV Changer Updates", message))
    def work():
        try:
            release = json.loads(get_bytes(API, 2_000_000))
            if version_parts(release["tag_name"]) <= version_parts(VERSION):
                if manual:
                    notify("You already have the latest version.")
                return
            files = {item["name"]:item for item in release.get("assets", [])}
            if ASSET not in files or "SHA256SUMS.txt" not in files:
                notify("New version found, but the portable Windows package isn't available yet.\n" + release["html_url"])
                return
            def offer():
                if messagebox.askyesno("Update available", "Version "+release["tag_name"]+" is available. Download and install?"):
                    threading.Thread(target=lambda: install(files[ASSET], files["SHA256SUMS.txt"], window),daemon=True).start()
            window.after(0, offer)
        except Exception as e:
            if manual:
                notify("Could not check updates:\n"+str(e))
    threading.Thread(target=work, daemon=True).start()

def install(asset, checksums, window):
    def error(msg):
        window.after(0, lambda: messagebox.showerror("Update failed", msg))
    try:
        if not getattr(sys, "frozen", False):
            raise RuntimeError("Auto-installation requires the packaged Windows application.")
        expected = None
        for line in get_bytes(checksums["browser_download_url"],100_000).decode().splitlines():
            parts=line.split()
            if len(parts)==2 and parts[1].lstrip("*")==ASSET:
                expected=parts[0].lower()
        if expected is None or len(expected)!=64:
            raise RuntimeError("Missing valid SHA256 manifest entry.")
        archive=get_bytes(asset["browser_download_url"])
        if hashlib.sha256(archive).hexdigest()!=expected:
            raise RuntimeError("SHA256 checksum mismatch. Update cancelled.")
        target=Path(sys.executable).resolve().parent
        # The updater only replaces a known onedir layout and never touches other folders.
        if not (target/"_internal").is_dir():
            raise RuntimeError("This version uses a new folder-based build. Install the portable ZIP manually once from GitHub Releases.")
        staging=Path(tempfile.mkdtemp(prefix="sg0hann-fov-"))
        newfolder=staging/"new"
        newfolder.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            entries=z.infolist()
            if len(entries)>3000:
                raise RuntimeError("Unexpected archive layout.")
            for info in entries:
                p=Path(info.filename)
                if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0]!="sg0hann-FOV-Changer":
                    raise RuntimeError("Invalid archive path.")
                if info.file_size>120_000_000:
                    raise RuntimeError("Unexpected archive member size.")
                destination=newfolder.joinpath(*p.parts[1:])
                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(info) as src, destination.open("wb") as dst:
                        shutil.copyfileobj(src,dst)
        if not (newfolder/"sg0hann-FOV-Changer.exe").is_file() or not (newfolder/"_internal").is_dir():
            raise RuntimeError("Unexpected app package structure.")
        # Stage new files on the same volume as installation to allow a fast folder swap.
        ready=target.parent/(target.name+".update-ready")
        if ready.exists():
            raise RuntimeError("Previous update staging folder exists: "+str(ready))
        shutil.copytree(newfolder,ready)
        script=staging/"finish.ps1"
        script.write_text(
            'param([int]$PreviousPid,[string]$Current,[string]$Ready)\n'
            'try { Wait-Process -Id $PreviousPid -ErrorAction SilentlyContinue } catch {}\n'
            'Start-Sleep -Milliseconds 1000\n'
            '$old = "$Current.update-backup"\n'
            'if (Test-Path -LiteralPath $old) { exit 2 }\n'
            'try {\n'
            '  Move-Item -LiteralPath $Current -Destination $old -ErrorAction Stop\n'
            '  try { Move-Item -LiteralPath $Ready -Destination $Current -ErrorAction Stop }\n'
            '  catch { Move-Item -LiteralPath $old -Destination $Current; throw }\n'
            '  Start-Process -FilePath (Join-Path $Current "sg0hann-FOV-Changer.exe")\n'
            '} catch { exit 1 }\n',
            encoding="utf-8")
        subprocess.Popen(["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass",
            "-File",str(script),"-PreviousPid",str(os.getpid()),"-Current",str(target),
            "-Ready",str(ready)],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),close_fds=True)
        window.after(0,window.destroy)
    except Exception as e:
        error(str(e))
