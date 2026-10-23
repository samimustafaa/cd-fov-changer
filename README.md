# sg0hann FOV Changer

Lightweight Windows **config-only prototype** with read-only detection of running `client.exe` and its install directory, with an FOV slider, presets, automatic backups, restore, and self-updates from GitHub Releases.

> **Important:** This is **not yet confirmed to work in Creative Destruction**. It only changes an existing FOV key in a configuration text file you select. It does not inject into the game or modify its memory.

## Download
Go to [Releases](https://github.com/samimustafaa/cd-fov-changer/releases/latest) and download **sg0hann-FOV-Changer-win64.zip**. Extract the entire ZIP, keeping the executable and `_internal` folder together.

## Features
- Automatically detects `client.exe` and reports likely config locations without scanning or changing process memory
- Prevents Apply/Restore while the game is running
- Slider 60–120 and 80 / 90 / 100 / 110 presets
- Edits one existing explicit FOV key in `.ini`, `.cfg`, or `.txt`
- Automatic config backup and restore
- Automatic check for new releases at app startup
- In-app update prompt: downloads the portable ZIP, verifies its SHA-256, safely replaces the installed app folder, and relaunches
- No injection, bypass, or game memory manipulation

## Development
Run `python app.py`. Build Windows exe with `pip install pyinstaller psutil` and `pyinstaller --onedir --windowed --name sg0hann-FOV-Changer app.py`.

## Releasing an update
Change `VERSION` in `updater.py` (e.g., `0.3.2`) and push to `main`. The Windows GitHub Actions workflow builds the EXE and creates a GitHub Release named `v0.1.1`. The app checks the latest release on startup and offers to update. If GitHub Actions is disabled, enable it for the repo.

**Note:** Running from Python cannot self-update. Downloaded EXE should be in a folder the user can write to, not Program Files.

## Active game files
When `client.exe` is running, use **Show active game file and module paths** for a read-only report of file handles and loaded module paths reported by Windows. Some entries may be unavailable. File paths don't expose camera FOV values. No injection, memory reading, patching, or anti-cheat bypass is performed.

## DLL error recovery
v0.3.1 switches from single-file EXE to a folder-based distribution after reports of missing `python312.dll` from temporary `_MEI` extraction. Download the new ZIP and extract it fully. Old v0.2.0 cannot repair itself if it does not launch. If Windows Security has quarantined a file, inspect Protection History; do not disable your protection.
