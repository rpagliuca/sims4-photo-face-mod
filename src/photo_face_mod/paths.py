from pathlib import Path

# the Mods/ subfolder the player drops the .ts4script, .package files and
# manifests into (see docs/instalacao.html)
MODS_FOLDER_NAME = "PhotoFaceMod"


def get_ts4_user_data_dir() -> Path:
    return Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"


def get_mod_dir() -> Path:
    return get_ts4_user_data_dir() / "Mods" / MODS_FOLDER_NAME
