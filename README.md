
# RegVapor

  

A lightweight, portable game launcher utility that resolves Windows Registry dependencies on the fly. It fetches unified configurations from a remote repository, maps execution paths dynamically, manages session-specific assets, and runs target games completely isolated inside a self-contained portable user profile.

  

## 🚀 Key Features

  

*  **Dynamic Registry Injection:** Pre-fills required keys, absolute folder paths (`{install_dir}` / `{install_src}`), and binary configurations directly into the Windows Registry before execution.

*  **True Isolation & Portability:** Redirects standard user folders (`AppData/Local`, `AppData/Roaming`, and `USERPROFILE`) into a localized `PortableProfile` folder within the game directory.

*  **Auto-Cleanup on Exit:** Dynamically backs up user configuration changes made during the session and purges the injected Windows Registry keys cleanly upon game exit.

*  **Transient File Modifiers (`.bak`):** Temporarily renames conflicting assets (e.g., troublesome intro videos or cache files) to `.bak` strings on startup and restores them seamlessly when the game closes.

*  **Session-Injected Fonts:** Automatically registers required custom game fonts into system memory for the duration of the play session without requiring administrative system installation.



  

## 🛠 How to Use It

  

1.  **Place the Launcher:** Drop the compiled `RegVapor` launcher executable directly into your target game's main installation folder (alongside the main game executable).

2.  **Set Your Game ID:** On the first run, the launcher will automatically generate a text file named `game_id.txt`. Open this file and type your unique case-sensitive profile identifier (e.g., `critical_point` or `chain_the_lost_footprints`).

3.  **Play:** Launch `RegVapor`. It will instantly pull down the configuration database, fix files, inject parameters, execute the game engine, and wait to perform structural cleanup when you quit.

  

  

## 📂 Managing configurations (`registry_src/`)

  

To add a new game profile or edit an existing configuration layout, do **not** modify `game_registry.json` directly. Pull Requests attempting to modify the root database directly are automatically blocked and closed by automated repository workflows.

  

Instead, create or update individual configuration profiles inside the `registry_src/` directory.

  

### Configuration Rules

* Every file inside `registry_src/` must be a valid JSON file ending in `.json`.

* Every entry must map exact registry type keywords (`REG_SZ`, `REG_BINARY`, or `REG_DWORD`) inside an array structure matching `["TYPE", "VALUE"]`.

*  **Path Tokens:** Use `{install_dir}` to dynamically represent the game's folder or `{install_src}` to represent its parent folder.

  

### Example JSON Template

Create your file inside `registry_src/your_game_id.json`:

  

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

*Note*: The `backup_files` array and `custom_font` keys are entirely optional.

### 💡 Troubleshooting & Extra Fixes
---
While **RegVapor** handles execution configurations, data structures, and environmental states, some legacy game engines require specific operating system media codecs to play back FMVs or cutscenes correctly.

### Video / Cutscene Issues Resolution

If a game crashes, throws a black screen, or hangs during intro videos (or videos look weird, like in Chain) and transitions:

1.  Download the **K-Lite Codec Pack Full** from the [Official Website](https://codecguide.com/download_k-lite_codec_pack_full.htm).
    
2.  Complete the standard installation, then open the **Codec Tweak Tool** bundled with the package.
    
3.  Locate and select the **Preferred decoders** settings panel.
    
4.  Manually configure the options for **MPEG-2, MPEG-1, DVSD, and MJPEG** to use **LAV filters** instead of Microsoft system handlers.
    
5.  Apply the changes for **both 32-bit and 64-bit** execution layouts.