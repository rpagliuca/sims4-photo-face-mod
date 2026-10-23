import json
from pathlib import Path
from typing import Dict, List, Optional, Union

PathLike = Union[str, "os.PathLike"]


class PhotoManifest:
    """Reads the photo_key -> CAS part id mappings written by the companion
    tool next to the .package files. Each photo is its own CASP; the companion
    tool stores its instance id as a "0x..." hex string.

    Given a directory, every `photo_manifest*.json` in it is merged (sorted by
    name), so the bundled collection (`photo_manifest_papelao.json`) and the
    player's own photos (`photo_manifest.json`) live side by side. Given a
    file, only that file is read.
    """

    def __init__(self, manifest_path: PathLike):
        self.manifest_path = Path(manifest_path)
        self._cache: Optional[Dict[str, str]] = None

    def reload(self) -> None:
        self._cache = None

    def _files(self) -> List[Path]:
        if self.manifest_path.is_dir():
            return sorted(self.manifest_path.glob("photo_manifest*.json"))
        return [self.manifest_path] if self.manifest_path.exists() else []

    def load(self) -> Dict[str, str]:
        if self._cache is None:
            merged: Dict[str, str] = {}
            for path in self._files():
                with open(path, "r", encoding="utf-8") as f:
                    merged.update(json.load(f))
            self._cache = merged
        return self._cache

    def cas_part_for(self, photo_key: str) -> Optional[int]:
        value = self.load().get(photo_key)
        if value is None:
            return None
        return int(value, 16) if isinstance(value, str) else int(value)

    def cas_part_ids(self) -> Dict[int, str]:
        """CAS part id -> photo_key, for every photo the mod knows."""
        return {self.cas_part_for(key): key for key in self.load()}

    def photo_keys(self) -> List[str]:
        return sorted(self.load().keys())
