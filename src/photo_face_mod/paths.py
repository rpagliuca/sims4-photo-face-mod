from pathlib import Path

MOD_NAME = "photo_face_mod"
ASSIGNMENTS_FILENAME = "assignments.json"
MANIFEST_FILENAME = "photo_manifest.json"


def get_ts4_user_data_dir() -> Path:
    return Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"


def get_mod_data_dir() -> Path:
    return get_ts4_user_data_dir() / "mod_data" / MOD_NAME


def get_manifest_path() -> Path:
    return get_ts4_user_data_dir() / "Mods" / MOD_NAME / MANIFEST_FILENAME
