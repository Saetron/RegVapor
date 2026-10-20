# Agent Development Guide (AGENTS.md)

Welcome to **RegVapor**. This document provides essential context, architecture details, and contribution rules for AI coding agents and automated tools working on this codebase.

---

## 1. Project Overview

**RegVapor** is a lightweight, portable game launcher utility for Windows. Its primary purpose is to allow legacy or portable Windows games requiring specific Windows Registry entries, custom session fonts, or transient asset replacements to run without permanent system modification or administrative installation.

### Key Behaviors
1. **Dynamic Registry Injection & Auto-Cleanup**: Injects required registry keys before launching the game, monitors game process execution, backs up user configuration changes upon game exit, and cleans up injected registry keys.
2. **Dynamic Path Tokens**: Expands `{install_dir}` (the game directory) and `{install_src}` (parent directory) inside registry string values at runtime.
3. **Session-Injected Fonts**: Temporarily loads custom fonts (e.g. `msgothic.ttc`) into process/system memory using Windows GDI without installing them globally.
4. **Transient File Backup (`.bak`)**: Temporarily renames conflicting files (such as problematic intro videos or codec crash triggers) to `.bak` before launch, and restores them when the game exits.
5. **Third-Party Integrations**: Integrates with [Locale-Emulator](https://github.com/xupefei/Locale-Emulator) and provides helper workflows for LAV Filters.

---

## 2. Repository Structure

```
RegVapor/
├── .github/
│   ├── scripts/
│   │   └── validate_json.py      # CI schema validation for registry_src/*.json
│   ├── workflows/
│   │   ├── block_registry_pr.yml # Blocks direct edits to game_registry.json
│   │   ├── build_launcher.yml    # PyInstaller compilation workflow (manual trigger)
│   │   ├── merge_registry.yml    # Compiles registry_src/*.json into game_registry.json
│   │   ├── update-locale-emulator.yml # Checks and updates Locale Emulator DLLs
│   │   └── validate_pr.yml       # Validates registry_src changes on pull requests
│   └── dependabot.yml            # Automated dependency updates for GitHub Actions
├── launcher/
│   ├── RegVapor.py               # Main launcher orchestrator entrypoint
│   ├── config.py                 # Core configuration, version, constants, path definitions
│   ├── file_handler.py           # Backup/restore logic for transient (.bak) files
│   ├── font_loader.py            # Windows GDI temporary font loader
│   ├── gui.py                    # Tkinter GUI (game selection dropdown, error modals)
│   ├── registry_handler.py       # Windows Registry injection and backup routines
│   ├── third_parties.py          # Third-party component utilities (LAV filters, etc.)
│   ├── updater.py                # Standalone updater executable
│   ├── utils.py                  # Structured logging utility
│   └── vapor_utils.py            # Remote registry fetching, caching, offline fallback
├── registry_src/                 # Source directory for game registry profiles
│   ├── 00_metadata.json          # Generated version metadata (do not edit manually)
│   └── <game_id>.json            # Individual game configuration profiles
├── third_party/
│   └── LocaleEmulator/           # Locale Emulator DLLs and license
├── game_registry.json            # COMPILED master registry file (DO NOT EDIT DIRECTLY)
├── LICENSE                       # EUPL-1.2 License
└── README.md                     # User-facing documentation
```

---

## 3. Critical Rules for Agents

### 🚨 Never Edit `game_registry.json` Directly
- `game_registry.json` is a **compiled artifact** generated automatically by `.github/workflows/merge_registry.yml` from `registry_src/*.json`.
- Pull Requests modifying `game_registry.json` directly are automatically blocked and closed by `block_registry_pr.yml`.
- **Always** make additions or changes to game configurations by adding or modifying individual JSON files inside `registry_src/`.

### 🚨 Run Schema Validation on Registry Profiles
Whenever modifying or adding a game profile in `registry_src/`, always run the validator script:

```bash
python3 .github/scripts/validate_json.py
```

Ensure it exits cleanly with code 0 (`✅ All source profiles validated cleanly!`).

---

## 4. Game Profile Format (`registry_src/<game_id>.json`)

Each profile inside `registry_src/` must be a valid JSON file with the following structure:

```json
{
  "your_game_id": {
    "key_path": "Software\\PublisherName\\GameTitle",
    "game_exe": "GAME_START.EXE",
    "registry_data": {
      "InstallDir": ["REG_SZ", "{install_dir}"],
      "VideoFolder": ["REG_SZ", ".\\"],
      "ConfigFlags": ["REG_BINARY", "01 00 00 00"],
      "ResolutionWidth": ["REG_DWORD", "1920"]
    },
    "backup_files": [
      "MOVIE/OpeningIntro.wmv"
    ],
    "custom_font": "msgothic.ttc"
  }
}
```

### Profile Field Requirements
- **Key (`your_game_id`)**: Unique lowercase identifier matching the file name without extension.
- **`key_path`** *(required, string)*: Registry subkey under `HKEY_CURRENT_USER`.
- **`game_exe`** *(required, string or array of strings)*: Name of the game executable(s) relative to the installation directory. If an array, RegVapor attempts to find the first existing candidate.
- **`registry_data`** *(required, object)*: Map of registry value names to `[TYPE, VALUE]` tuples:
  - Allowed types: `"REG_SZ"`, `"REG_BINARY"`, `"REG_DWORD"`.
  - Allowed path tokens: `{install_dir}` (game directory), `{install_src}` (parent directory).
- **`backup_files`** *(optional, array of strings)*: List of file paths to temporarily rename to `.bak` while the game runs.
- **`custom_font`** *(optional, string)*: Relative path to a font file to load in-memory for the session.

---

## 5. Development Guidelines for `launcher/` Code

- **Python Version**: Target Python 3.10+ (CI runs on Python 3.13).
- **Windows API Compatibility**: Note that modules such as `winreg` or `ctypes.windll` are Windows-specific. When writing or testing code on non-Windows environments (macOS/Linux), use appropriate guards or mocks if executing unit tests locally.
- **Version Bumping**: The version number is defined in `launcher/config.py`:
  ```python
  __version__ = "0.6.5"
  ```
  Updating `__version__` will propagate to the launcher UI, logs, generated metadata, and release tags.
- **Logging**: Use `utils.log_message(msg, *args)` instead of raw `print` statements in the launcher codebase.
- **Executable Compilation**:
  Executable releases are built using PyInstaller on Windows:
  ```bash
  pyinstaller --noconsole --onefile --name=RegVapor launcher/RegVapor.py
  pyinstaller --noconsole --onefile --name=RegVapor_updater launcher/updater.py
  ```
  The GitHub Action workflow (`.github/workflows/build_launcher.yml`) is triggered manually via `workflow_dispatch`.
