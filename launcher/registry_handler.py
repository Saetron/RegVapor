from pathlib import Path
import winreg


def delete_key(root: int, subkey: str) -> None:
    """Recursively purges a registry branch completely from Windows."""
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    child = winreg.EnumKey(key, 0)
                    delete_key(key, child)
                except OSError:
                    break
    except FileNotFoundError:
        return
    winreg.DeleteKey(root, subkey)


def set_key(game_dir: Path, backup_dir: Path, entry: dict) -> None:
    """Injects saved local states or default layouts, matching active path states."""
    key_path = entry.get("key_path", "")
    registry_data = entry.get("registry_data", {})

    if not key_path or not registry_data:
        return

    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
    ) as key:
        for value_name, (type_str, default_val) in registry_data.items():
            default_str = str(default_val)

            if type_str == "REG_BINARY":
                data_type = winreg.REG_BINARY
                fallback_val: bytes | int | str = bytes.fromhex(
                    default_str.replace(" ", "")
                )
            elif type_str == "REG_DWORD":
                data_type = winreg.REG_DWORD
                fallback_val = int(default_str.strip())
            else:
                data_type = winreg.REG_SZ
                fallback_val = default_str

            is_path_key = (
                "{install_dir}" in default_str
                or "{install_src}" in default_str
                or default_str == ".\\"
            )

            backup_file = backup_dir / f"{value_name}.regdata"
            if backup_file.exists() and not is_path_key:
                try:
                    if data_type == winreg.REG_BINARY:
                        prepared_value: bytes | int | str = backup_file.read_bytes()
                    elif data_type == winreg.REG_DWORD:
                        prepared_value = int(
                            backup_file.read_text(encoding="utf-8").strip()
                        )
                    else:
                        prepared_value = backup_file.read_text(encoding="utf-8")
                except Exception:
                    prepared_value = fallback_val
            elif "{install_dir}" in default_str or "{install_src}" in default_str:
                prepared_value = default_str.replace(
                    "{install_dir}", str(game_dir)
                ).replace("{install_src}", str(game_dir.parent))
            else:
                prepared_value = fallback_val

            winreg.SetValueEx(key, value_name, 0, data_type, prepared_value)


def backup(key_path: str, backup_dir: Path) -> None:
    """Harvests user adjustments into files and deletes the Windows keys completely."""
    if not key_path:
        return

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ
        ) as key:
            index = 0
            while True:
                try:
                    value_name, value_data, data_type = winreg.EnumValue(key, index)
                except OSError:
                    break

                backup_file = backup_dir / f"{value_name}.regdata"
                if data_type == winreg.REG_BINARY:
                    backup_file.write_bytes(value_data)
                else:
                    backup_file.write_text(str(value_data), encoding="utf-8")

                index += 1
    except FileNotFoundError:
        return

    delete_key(winreg.HKEY_CURRENT_USER, key_path)
