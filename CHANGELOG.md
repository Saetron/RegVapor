# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Added `AGENTS.md` providing development guidelines and mandatory practices for AI coding agents.
- Added Dependabot configuration (`.github/dependabot.yml`) for tracking GitHub Actions workflow updates.

### Changed
- Bumped `actions/checkout` from v4 to v7 across CI workflows.
- Bumped `actions/setup-python` from v5 to v7 across CI workflows.
- Bumped `actions/github-script` from v7 to v9 in `block_registry_pr.yml`.
- Bumped `softprops/action-gh-release` from v2 to v3 in `build_launcher.yml`.
- Converted release creation GitHub Actions workflow (`build_launcher.yml`) to run exclusively on manual trigger (`workflow_dispatch`).

### Removed
- Removed pre-commit configuration (`.pre-commit-config.yaml`) and CI check workflow (`.github/workflows/pre-commit.yml`).

---

## [0.6.5] - 2026-07-18

### Added
- Added LAV Filters download utility (`launcher/third_parties.py`).
- Added automated GitHub Actions workflow to check and update Locale Emulator DLLs (`.github/workflows/update-locale-emulator.yml`).
- Added third-party components section and codec guidance to `README.md`.

### Fixed
- Fixed GitHub license auto-detection.
- Fixed DLL extraction and casing in Locale Emulator update workflow.
- Fixed remote version detection logic.

---

## [0.6.4] - 2026-07-16

### Added
- Created dedicated `file_handler.py` module for transient (`.bak`) file backup and restoration.
- Modularized launcher script components into distinct helper modules.

### Fixed
- Improved robustness and path resolution of the standalone updater.
- Added post-execution cleanup logic for updater processes.

---

## [0.6.3] - 2026-07-15

### Changed
- Separated update checking logic from common utilities into dedicated modules.
- Refined automated master registry compilation metadata and version tracking.

---

## [0.6.2] - 2026-07-15

### Added
- Added cleanup routines for the standalone updater process.

---

## [0.6.1] - 2026-07-14

### Added
- Built standalone updater executable logic (`launcher/updater.py`).

### Fixed
- Resolved GitHub Actions script configuration issues.

---

## [0.6.0] - 2026-07-14

### Added
- Migrated launcher codebase to a modular architecture (`config.py`, `gui.py`, `vapor_utils.py`, `utils.py`, `registry_handler.py`).
- Added structured logging mechanism (`utils.log_message`) replacing raw `print` statements.
- Added Tkinter-based graphical user interface for selecting game profiles from available IDs.
- Isolated launcher configuration directory under `RegVapor/`.

---

## [0.5.0] - 2026-07-13

### Added
- Added offline fallback support for the game registry database (`RegVapor_game.json`).
- Added support for multiple executable candidate paths per game profile.
- Added session-injected font loader (`font_loader.py`) utilizing Windows GDI APIs.
- Added transient file backup and restoration system (`backup_files`).
- Added automated CI workflows for registry merging, PR validation, and PR blocking.
- Initial game registry profiles: Critical Point, Yumina, Snow Drop, Princess Waltz, Figures of Happiness, Chain The Lost Footprints, Crescendo, Guilty The Sin, We Love Master.
