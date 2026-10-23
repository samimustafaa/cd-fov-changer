"""Read-only Windows client.exe detection. No process handles with write permissions."""
from pathlib import Path
try:
    import psutil
except ImportError:
    psutil = None

def detect_client():
    if psutil is None:
        return None
    for proc in psutil.process_iter(["pid","name","exe"]):
        try:
            if (proc.info.get("name") or "").lower() == "client.exe":
                return {"pid":proc.info["pid"],"exe":proc.info.get("exe") or ""}
        except (psutil.AccessDenied,psutil.NoSuchProcess,psutil.ZombieProcess):
            continue
    return None

def inspect_game_folder(exe):
    """Only report names of probable configuration files; never parse protected data."""
    if not exe:
        return "client.exe detected, but Windows did not provide its location."
    folder=Path(exe).parent
    candidates=[]
    for relative in ("options.ini","options","config","Config","Documents","Documents/UserData"):
        candidate=folder / relative
        if candidate.exists():
            candidates.append(str(candidate))
    return ("Installation: "+str(folder)+"\n\nExisting config candidates:\n"+
            ("\n".join(candidates) if candidates else "None found")+
            "\n\nNo FOV field has been verified. No memory or game files were changed.")
