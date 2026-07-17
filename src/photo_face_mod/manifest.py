import json
from pathlib import Path
from typing import Dict, List, Optional, Union

PathLike = Union[str, "os.PathLike"]


class PhotoManifest:
    """Reads the photo_key -> swatch_index mapping baked by the companion
    tool into the .package (photo_manifest.json, shipped alongside it).
    """

    def __init__(self, manifest_path: PathLike):
        self.manifest_path = Path(manifest_path)
        self._cache: Optional[Dict[str, int]] = None

    def reload(self) -> None:
        self._cache = None

    def load(self) -> Dict[str, int]:
        if self._cache is None:
            if not self.manifest_path.exists():
                self._cache = {}
            else:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        return self._cache

    def swatch_for(self, photo_key: str) -> Optional[int]:
        return self.load().get(photo_key)

    def photo_keys(self) -> List[str]:
        return list(self.load().keys())
