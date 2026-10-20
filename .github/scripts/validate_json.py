import json
from pathlib import Path
import sys

ALLOWED_TYPES = {"REG_SZ", "REG_BINARY", "REG_DWORD"}
REQUIRED_KEYS = ("game_exe", "key_path", "registry_data")


def validate_profile_structure(profile: dict) -> bool:
    errors_found = False

    for key in REQUIRED_KEYS:
        if key not in profile:
            print(f"  └── ❌ Missing required key: '{key}'")
            errors_found = True

    if errors_found:
        return False

    if not isinstance(profile["key_path"], str):
        print("  └── ❌ 'key_path' must be a string.")
        errors_found = True

    game_exe = profile["game_exe"]
    if not isinstance(game_exe, str) and not (
        isinstance(game_exe, list)
        and game_exe
        and all(isinstance(x, str) for x in game_exe)
    ):
        print("  └── ❌ 'game_exe' must be a string or a non-empty list of strings.")
        errors_found = True

    reg_data = profile["registry_data"]
    if not isinstance(reg_data, dict):
        print("  └── ❌ 'registry_data' must be a nested JSON object {}")
        return False

    for value_name, entry in reg_data.items():
        if not isinstance(entry, list) or len(entry) != 2:
            print(
                f'  └── ❌ Value \'{value_name}\' must be an array matching ["TYPE", "VALUE"].'
            )
            errors_found = True
            continue

        reg_type, _ = entry
        if reg_type not in ALLOWED_TYPES:
            print(
                f"  └── ❌ Value '{value_name}' has an invalid registry type '{reg_type}'. Must be one of {ALLOWED_TYPES}."
            )
            errors_found = True

    if "backup_files" in profile:
        if not isinstance(profile["backup_files"], list):
            print(
                '  └── ❌ \'backup_files\' must be a JSON array ["file1.dat", "file2.txt"]'
            )
            errors_found = True
        else:
            for item in profile["backup_files"]:
                if not isinstance(item, str):
                    print(
                        f"  └── ❌ 'backup_files' items must be strings. Found type: {type(item).__name__}"
                    )
                    errors_found = True

    if "custom_font" in profile and not isinstance(profile["custom_font"], str):
        print("  └── ❌ 'custom_font' must be a string.")
        errors_found = True

    return not errors_found


def main() -> None:
    source_dir = Path("registry_src")
    print("=== Starting RegVapor Source Files Schema Validation ===")

    if not source_dir.is_dir():
        print(f"❌ Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)

    json_files = sorted(source_dir.glob("*.json"))
    if not json_files:
        print(f"⚠️ Warning: No JSON files found inside '{source_dir}/'. Skipping check.")
        sys.exit(0)

    total_errors = 0
    for file_path in json_files:
        print(f"\nScanning source file: {file_path.name}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON syntax in file:\n{e}")
            total_errors += 1
            continue

        if not isinstance(content, dict):
            print("❌ Error: Top-level file structure must be a JSON object.")
            total_errors += 1
            continue

        for game_id, profile in content.items():
            if game_id == "__metadata__":
                continue
            print(f"  Checking game profile definition: [{game_id}]")
            if not isinstance(profile, dict):
                print(
                    f"    └── ❌ Profile value for '{game_id}' must be an object structure."
                )
                total_errors += 1
                continue

            if not validate_profile_structure(profile):
                total_errors += 1

    print("\n=======================================================")
    if total_errors > 0:
        print(f"❌ Validation Failed! Found {total_errors} structural error(s).")
        sys.exit(1)

    print("✅ All source profiles validated cleanly!")
    sys.exit(0)


if __name__ == "__main__":
    main()
