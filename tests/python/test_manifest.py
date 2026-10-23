import json

from photo_face_mod.manifest import PhotoManifest


def _write_manifest(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_cas_part_for_known_key_parses_hex(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"fulano": "0x9D09F8AE8D0CEC54", "ciclano": "0x0000000000000002"})
    manifest = PhotoManifest(manifest_path)
    assert manifest.cas_part_for("fulano") == 0x9D09F8AE8D0CEC54
    assert manifest.cas_part_for("ciclano") == 2


def test_cas_part_for_accepts_plain_ints(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"fulano": 7})
    assert PhotoManifest(manifest_path).cas_part_for("fulano") == 7


def test_cas_part_for_unknown_key_returns_none(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"fulano": "0x1"})
    assert PhotoManifest(manifest_path).cas_part_for("desconhecido") is None


def test_missing_manifest_file_behaves_as_empty(tmp_path):
    manifest = PhotoManifest(tmp_path / "does_not_exist.json")
    assert manifest.load() == {}
    assert manifest.photo_keys() == []


def test_photo_keys_lists_all_entries(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"fulano": "0x1", "ciclano": "0x2"})
    assert sorted(PhotoManifest(manifest_path).photo_keys()) == ["ciclano", "fulano"]


def test_load_is_cached_until_reload(tmp_path):
    manifest_path = tmp_path / "photo_manifest.json"
    _write_manifest(manifest_path, {"fulano": "0x1"})
    manifest = PhotoManifest(manifest_path)
    assert manifest.cas_part_for("fulano") == 1

    _write_manifest(manifest_path, {"fulano": "0x9"})
    assert manifest.cas_part_for("fulano") == 1

    manifest.reload()
    assert manifest.cas_part_for("fulano") == 9


def test_a_directory_merges_every_photo_manifest_file(tmp_path):
    _write_manifest(tmp_path / "photo_manifest_papelao.json", {"pirata": "0x1", "robo": "0x2"})
    _write_manifest(tmp_path / "photo_manifest.json", {"foto": "0x3"})
    _write_manifest(tmp_path / "outro.json", {"ignorado": "0x9"})
    manifest = PhotoManifest(tmp_path)
    assert manifest.photo_keys() == ["foto", "pirata", "robo"]
    assert manifest.cas_part_ids() == {1: "pirata", 2: "robo", 3: "foto"}
