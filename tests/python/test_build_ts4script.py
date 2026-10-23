import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "build"))

import build_ts4script  # noqa: E402


def test_build_produces_valid_zip(tmp_path):
    output = build_ts4script.build(tmp_path / "photofacemod.ts4script")
    assert output.exists()
    assert zipfile.is_zipfile(output)


def test_build_contains_expected_pyc_files(tmp_path):
    output = build_ts4script.build(tmp_path / "photofacemod.ts4script")
    with zipfile.ZipFile(output) as zf:
        names = set(zf.namelist())
    assert "mod_entrypoint.pyc" in names
    assert "photo_face_mod/__init__.pyc" in names
    assert "photo_face_mod/manifest.pyc" in names
    assert "photo_face_mod/ts4_integration.pyc" in names
    assert all(name.endswith(".pyc") for name in names)


def test_build_leaves_no_pyc_files_behind_in_src(tmp_path):
    build_ts4script.build(tmp_path / "photofacemod.ts4script")
    # Only checks the compiler's own output location (alongside each .py),
    # not Python's unrelated __pycache__/ import cache created by pytest itself.
    leftovers = [p for p in build_ts4script.SRC_DIR.rglob("*.pyc") if p.parent.name != "__pycache__"]
    assert leftovers == []
