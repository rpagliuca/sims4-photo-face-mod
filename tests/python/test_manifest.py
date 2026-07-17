import json

from photo_face_mod.manifest import PhotoManifest


def _write_manifest(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_swatch_for_known_key(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": 0, "irmao": 1})
    manifest = PhotoManifest(manifest_path)
    assert manifest.swatch_for("rafael") == 0
    assert manifest.swatch_for("irmao") == 1


def test_swatch_for_unknown_key_returns_none(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": 0})
    manifest = PhotoManifest(manifest_path)
    assert manifest.swatch_for("desconhecido") is None


def test_missing_manifest_file_behaves_as_empty(tmp_path):
    manifest = PhotoManifest(tmp_path / "does_not_exist.json")
    assert manifest.load() == {}
    assert manifest.photo_keys() == []


def test_photo_keys_lists_all_entries(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": 0, "irmao": 1})
    manifest = PhotoManifest(manifest_path)
    assert sorted(manifest.photo_keys()) == ["irmao", "rafael"]


def test_load_is_cached_until_reload(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": 0})
    manifest = PhotoManifest(manifest_path)
    assert manifest.swatch_for("rafael") == 0

    _write_manifest(manifest_path, {"rafael": 9})
    assert manifest.swatch_for("rafael") == 0

    manifest.reload()
    assert manifest.swatch_for("rafael") == 9
