import subprocess
import config
import file_handler
import font_loader as font
import gui
import registry_handler as registry
from utils import log_message as log
import vapor_utils as vapor


def main() -> None:
    config.backup_dir.mkdir(parents=True, exist_ok=True)
    log("RegVapor Version {}", config.__version__)

    game_id = vapor.read_saved_game_id()
    master_config = vapor.get_master_config()

    if master_config:
        vapor.check_for_updates(master_config)

    master_config = vapor.fetch_and_cache_config(game_id, master_config)

    if not game_id:
        if not master_config:
            gui.show_error_message(
                "Could not fetch configuration database (online or offline fallback), and no local configuration file exists."
            )
            return

        available_ids = sorted(k for k in master_config if k != "__metadata__")
        game_id = gui.select_game_id_gui(available_ids)

        if not game_id:
            return
        file_handler.game_id_write(game_id, master_config)

    log("RegVapor Launcher v{} initializing for ID: {}", config.__version__, game_id)

    if not master_config or game_id not in master_config:
        log("Error: Configurations for '{}' not found.", game_id)
        return

    entry = master_config[game_id]
    key_path = entry.get("key_path", "")

    game_exe_setting = entry["game_exe"]
    exe_candidates = (
        [game_exe_setting] if isinstance(game_exe_setting, str) else game_exe_setting
    )

    game_exe = next(
        (
            target_path
            for candidate in exe_candidates
            if (target_path := config.base_dir / candidate).exists()
        ),
        None,
    )

    if not game_exe:
        log(
            "Executable missing. Looked for: {} inside {}",
            exe_candidates,
            config.base_dir,
        )
        return

    font_loaded = False
    font_path = None
    font_filename = entry.get("custom_font")
    if font_filename:
        font_path = config.base_dir / font_filename
        font_loaded = font.load(font_path)

    active_backups = []
    backup_files_list = entry.get("backup_files", [])
    if backup_files_list and isinstance(backup_files_list, list):
        active_backups = file_handler.backup(config.base_dir, backup_files_list)

    try:
        registry.set_key(config.base_dir, config.backup_dir, entry)
    except Exception as e:
        log("Failed setting registry parameters: {}", e)

    try:
        subprocess.run([str(game_exe)], cwd=str(config.base_dir))
    except Exception as e:
        log("Engine failed to run execution loops: {}", e)
    finally:
        try:
            registry.backup(key_path, config.backup_dir)
        except Exception as e:
            log("Scrub and backup failure: {}", e)

        if active_backups:
            file_handler.restore(active_backups)

        if font_loaded and font_path:
            font.unload(font_path)


if __name__ == "__main__":
    main()
