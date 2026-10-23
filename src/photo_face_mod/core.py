import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, Union

PathLike = Union[str, os.PathLike]


class PhotoAssignmentStore:
    """Persists which photo CAS part (CASP instance id) is assigned to each Sim.

    Keyed by sim_id alone (no save-slot bucketing): a Sim's sim_id is a
    globally unique identifier assigned once per Sim instance and stable
    across save/load of the same save file, so it already disambiguates
    Sims without needing to track which save slot is active.
    """

    def __init__(self, data_dir: PathLike, filename: str = "assignments.json"):
        self.data_dir = Path(data_dir)
        self.filename = filename

    @property
    def _path(self) -> Path:
        return self.data_dir / self.filename

    def _load(self) -> Dict[str, int]:
        if not self._path.exists():
            return {}
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict[str, int]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self.data_dir, prefix=".tmp_assignments_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
            os.replace(tmp_path, self._path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def assign(self, sim_id: Union[str, int], cas_part_id: int) -> None:
        data = self._load()
        data[str(sim_id)] = cas_part_id
        self._save(data)

    def get(self, sim_id: Union[str, int]) -> Optional[int]:
        return self._load().get(str(sim_id))

    def remove(self, sim_id: Union[str, int]) -> bool:
        data = self._load()
        if str(sim_id) not in data:
            return False
        del data[str(sim_id)]
        self._save(data)
        return True

    def all(self) -> Dict[str, int]:
        return self._load()
