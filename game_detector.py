"""Read-only process metadata and on-disk configuration discovery for client.exe."""
from pathlib import Path
try:
    import psutil
except ImportError:
    psutil = None

def detect_client():
    if not psutil:
        return None
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            if (proc.info.get("name") or "").lower() == "client.exe":
                return {"pid": proc.pid, "exe": proc.info.get("exe") or ""}
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
    return None

def inspect_game_folder(exe):
    if not exe:
        return "client.exe detected but its install location is unavailable."
    root=Path(exe).parent
    result=["Installation directory: "+str(root)]
    for folder in [root,root/"Documents",root/"Documents"/"UserData",root/"ccmini"]:
        if not folder.is_dir():
            continue
        result.append("\n"+str(folder)+":")
        try:
            items=sorted(folder.iterdir(),key=lambda p:p.name.lower())
            for item in items[:55]:
                result.append("  "+("[dir] " if item.is_dir() else "[file] ")+item.name)
            if len(items)>55:result.append("  ... more items omitted")
        except OSError as e:result.append("  Not readable: "+str(e))
    result.append("\nFiles are listed only. Nothing has been modified.")
    return "\n".join(result)

def inspect_process_files(pid):
    """Read-only listing: open file handles and loaded module paths, when Windows permits."""
    if psutil is None:
        return "psutil is unavailable."
    try:
        proc=psutil.Process(pid)
        if proc.name().lower()!="client.exe":
            return "Target is no longer client.exe."
        exe=proc.exe()
        lines=["client.exe • process ID: "+str(pid),"Executable: "+exe]
        try:
            handles=sorted({f.path for f in proc.open_files() if f.path})
            lines.append("\nOpen files reported by Windows ("+str(len(handles))+"):")
            lines.extend("  "+x for x in handles[:90])
            if len(handles)>90:lines.append("  ... additional entries omitted")
        except (psutil.AccessDenied,psutil.NoSuchProcess,OSError) as e:
            lines.append("\nOpen-file metadata unavailable: "+str(e))
        try:
            mapped=sorted({m.path for m in proc.memory_maps(grouped=True) if m.path})
            lines.append("\nLoaded module/file paths ("+str(len(mapped))+"):")
            lines.extend("  "+x for x in mapped[:90])
            if len(mapped)>90:lines.append("  ... additional entries omitted")
        except (psutil.AccessDenied,psutil.NoSuchProcess,OSError) as e:
            lines.append("\nModule metadata unavailable: "+str(e))
        lines.append("\nThis lists OS-reported file paths only. No file contents, game memory, or FOV values are accessed.")
        return "\n".join(lines)
    except (psutil.AccessDenied,psutil.NoSuchProcess,OSError) as e:
        return "Cannot read process metadata: "+str(e)
