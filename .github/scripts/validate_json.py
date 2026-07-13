import sys
import json
from pathlib import Path

def validate_profile_structure(profile: dict, file_name: str) -> bool:
    """Validates an individual game profile configuration structure."""
    allowed_types = {"REG_SZ", "REG_BINARY", "REG_DWORD"}
    errors_found = False

    # 1. Verify mandatory top-level keys
    required_keys = ["game_exe", "key_path", "registry_data"]
    for key in required_keys:
        if key not in profile:
            print(f"  └── ❌ Missing required key: '{key}'")
            errors_found = True

    if errors_found:
        return False

    # 2. Verify registry_data block structure
    reg_data = profile["registry_data"]
    if not isinstance(reg_data, dict):
        print("  └── ❌ 'registry_data' must be a nested JSON object {}")
        return False

    # 3. Verify individual registry elements
    for value_name, entry in reg_data.items():
        if not isinstance(entry, list) or len(entry) != 2:
            print(f"  └── ❌ Value '{value_name}' must be an array matching [\"TYPE\", \"VALUE\"].")
            errors_found = True
            continue

        reg_type, _ = entry
        if reg_type not in allowed_types:
            print(f"  └── ❌ Value '{value_name}' has an invalid registry type '{reg_type}'. Must be one of {allowed_types}.")
            errors_found = True

    return not errors_found

def main():
    source_dir = Path("registry_src")
    
    print("=== Starting RegVapor Source Files Schema Validation ===")
    
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"❌ Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)

    json_files = list(source_dir.glob("*.json"))
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

        # Each file can contain one or multiple game profile dictionaries
        for game_id, profile in content.items():
            print(f"  Checking game profile definition: [{game_id}]")
            if not isinstance(profile, dict):
                print(f"    └── ❌ Profile value for '{game_id}' must be an object structure.")
                total_errors += 1
                continue
                
            if not validate_profile_structure(profile, file_path.name):
                total_errors += 1

    print(f"\n=======================================================")
    if total_errors > 0:
        print(f"❌ Validation Failed! Found {total_errors} structural error(s) across your source files.")
        sys.exit(1)
        
    print("✅ All source profiles validated cleanly! Ready to merge and compile.")
    sys.exit(0)

if __name__ == "__main__":
    main()