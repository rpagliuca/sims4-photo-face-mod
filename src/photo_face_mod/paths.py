from pathlib import Path

# snake_case: internal mod_data folder name (not player-facing)
MOD_NAME = "photo_face_mod"
# PascalCase: the Mods/ subfolder the player creates and drops the
# .ts4script/.package/manifest into (see docs/instalacao.html)
MODS_FOLDER_NAME = "PhotoFaceMod"
ASSIGNMENTS_FILENAME = "assignments.json"
MANIFEST_FILENAME = "photo_manifest.json"


def get_ts4_user_data_dir() -> Path:
    return Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"


def get_mod_data_dir() -> Path:
    return get_ts4_user_data_dir() / "mod_data" / MOD_NAME


def get_manifest_path() -> Path:
    return get_ts4_user_data_dir() / "Mods" / MODS_FOLDER_NAME / MANIFEST_FILENAME
