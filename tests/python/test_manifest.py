import json

from photo_face_mod.manifest import PhotoManifest


def _write_manifest(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_cas_part_for_known_key_parses_hex(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": "0x9D09F8AE8D0CEC54", "irmao": "0x0000000000000002"})
    manifest = PhotoManifest(manifest_path)
    assert manifest.cas_part_for("rafael") == 0x9D09F8AE8D0CEC54
    assert manifest.cas_part_for("irmao") == 2


def test_cas_part_for_accepts_plain_ints(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": 7})
    assert PhotoManifest(manifest_path).cas_part_for("rafael") == 7


def test_cas_part_for_unknown_key_returns_none(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": "0x1"})
    assert PhotoManifest(manifest_path).cas_part_for("desconhecido") is None


def test_missing_manifest_file_behaves_as_empty(tmp_path):
    manifest = PhotoManifest(tmp_path / "does_not_exist.json")
    assert manifest.load() == {}
    assert manifest.photo_keys() == []


def test_photo_keys_lists_all_entries(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": "0x1", "irmao": "0x2"})
    assert sorted(PhotoManifest(manifest_path).photo_keys()) == ["irmao", "rafael"]


def test_load_is_cached_until_reload(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"rafael": "0x1"})
    manifest = PhotoManifest(manifest_path)
    assert manifest.cas_part_for("rafael") == 1

    _write_manifest(manifest_path, {"rafael": "0x9"})
    assert manifest.cas_part_for("rafael") == 1

    manifest.reload()
    assert manifest.cas_part_for("rafael") == 9
