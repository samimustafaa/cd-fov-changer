# sg0hann FOV Changer

Lightweight Windows **config-only prototype** with read-only detection of running `client.exe` and its install directory, with an FOV slider, presets, automatic backups, restore, and self-updates from GitHub Releases.

> **Important:** This is **not yet confirmed to work in Creative Destruction**. It only changes an existing FOV key in a configuration text file you select. It does not inject into the game or modify its memory.

## Download
Go to [Releases](https://github.com/samimustafaa/cd-fov-changer/releases/latest) and download **sg0hann-FOV-Changer.exe**.

## Features
- Automatically detects `client.exe` and reports likely config locations without scanning or changing process memory
- Prevents Apply/Restore while the game is running
- Slider 60–120 and 80 / 90 / 100 / 110 presets
- Edits one existing explicit FOV key in `.ini`, `.cfg`, or `.txt`
- Automatic config backup and restore
- Automatic check for new releases at app startup
- In-app update prompt: downloads the replacement EXE, verifies SHA-256 against release checksums, closes the app, replaces its own executable, and relaunches it
- No injection, bypass, or game memory manipulation

## Development
Run `python app.py`. Build Windows exe with `pip install pyinstaller` and `pyinstaller --onefile --windowed --name sg0hann-FOV-Changer app.py`.

## Releasing an update
Change `VERSION` in `updater.py` (e.g., `0.2.1`) and push to `main`. The Windows GitHub Actions workflow builds the EXE and creates a GitHub Release named `v0.1.1`. The app checks the latest release on startup and offers to update. If GitHub Actions is disabled, enable it for the repo.

**Note:** Running from Python cannot self-update. Downloaded EXE should be in a folder the user can write to, not Program Files.
