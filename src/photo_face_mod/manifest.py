import json
from pathlib import Path
from typing import Dict, List, Optional, Union

PathLike = Union[str, "os.PathLike"]


class PhotoManifest:
    """Reads the photo_key -> CAS part id mapping written by the companion
    tool next to the .package (photo_manifest.json). Each photo is its own
    CASP; the companion tool stores its instance id as a "0x..." hex string.
    """

    def __init__(self, manifest_path: PathLike):
        self.manifest_path = Path(manifest_path)
        self._cache: Optional[Dict[str, str]] = None

    def reload(self) -> None:
        self._cache = None

    def load(self) -> Dict[str, str]:
        if self._cache is None:
            if not self.manifest_path.exists():
                self._cache = {}
            else:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        return self._cache

    def cas_part_for(self, photo_key: str) -> Optional[int]:
        value = self.load().get(photo_key)
        if value is None:
            return None
        return int(value, 16) if isinstance(value, str) else int(value)

    def photo_keys(self) -> List[str]:
        return list(self.load().keys())
