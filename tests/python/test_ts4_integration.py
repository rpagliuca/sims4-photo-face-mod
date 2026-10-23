import json

import sims4.commands as fake_commands
import services as fake_services
from server_commands import argument_helpers as fake_argument_helpers

from fakes import FakeSim
from photo_face_mod import ts4_integration
from photo_face_mod.core import PhotoAssignmentStore
from photo_face_mod.manifest import PhotoManifest

PHOTO_A = 0x9D09F8AE8D0CEC54
PHOTO_B = 0x8000000000000002
GLASSES = 11


def _write_manifest(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def _use(monkeypatch, tmp_path, manifest_data=None):
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, manifest_data or {})
    monkeypatch.setattr(ts4_integration, "manifest", PhotoManifest(manifest_path))
    store = PhotoAssignmentStore(tmp_path / "data")
    monkeypatch.setattr(ts4_integration, "store", store)
    return store


def test_assign_photo_with_no_sim_selected_reports_error():
    fake_argument_helpers.get_optional_target_result = None
    result = ts4_integration.assign_photo("fulano", None, _connection=None)
    assert result is False
    assert any("nenhum Sim selecionado" in msg for msg in fake_commands.output_calls)


def test_assign_photo_unknown_key_reports_error(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path)
    fake_argument_helpers.get_optional_target_result = fake_sim
    result = ts4_integration.assign_photo("desconhecido", None, _connection=None)
    assert result is False
    assert any("nao encontrada" in msg for msg in fake_commands.output_calls)


def test_assign_photo_puts_the_cas_part_on_every_outfit_replacing_glasses(tmp_path, monkeypatch, fake_sim):
    store = _use(monkeypatch, tmp_path, {"fulano": "0x%016X" % PHOTO_A})
    fake_argument_helpers.get_optional_target_result = fake_sim

    result = ts4_integration.assign_photo("fulano", None, _connection=None)

    assert result is True
    assert store.get(fake_sim.sim_info.sim_id) == PHOTO_A
    assert fake_sim.sim_info.outfit_parts() == [[1001, PHOTO_A], [1002, PHOTO_A]]
    assert fake_sim.sim_info._outfits[0][1] == (PHOTO_A, GLASSES)
    assert fake_sim.sim_info.resend_count == 1
    assert any("atribuida" in msg for msg in fake_commands.output_calls)


def test_assigning_another_photo_swaps_the_part(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, {"a": "0x%016X" % PHOTO_A, "b": "0x%016X" % PHOTO_B})
    fake_argument_helpers.get_optional_target_result = fake_sim
    ts4_integration.assign_photo("a", None, _connection=None)
    ts4_integration.assign_photo("b", None, _connection=None)
    assert fake_sim.sim_info.outfit_parts() == [[1001, PHOTO_B], [1002, PHOTO_B]]


def test_remove_photo_takes_the_part_off(tmp_path, monkeypatch, fake_sim):
    store = _use(monkeypatch, tmp_path, {"fulano": "0x%016X" % PHOTO_A})
    fake_argument_helpers.get_optional_target_result = fake_sim
    ts4_integration.assign_photo("fulano", None, _connection=None)

    result = ts4_integration.remove_photo(None, _connection=None)

    assert result is True
    assert store.get(fake_sim.sim_info.sim_id) is None
    assert fake_sim.sim_info.outfit_parts() == [[1001], [1002]]
    assert any("removida" in msg for msg in fake_commands.output_calls)


def test_remove_photo_when_none_assigned(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path)
    fake_argument_helpers.get_optional_target_result = fake_sim

    result = ts4_integration.remove_photo(None, _connection=None)

    assert result is True
    assert fake_sim.sim_info.resend_count == 0
    assert any("nao tinha foto" in msg for msg in fake_commands.output_calls)


def test_list_photos_outputs_available_keys(tmp_path, monkeypatch):
    _use(monkeypatch, tmp_path, {"fulano": "0x1", "ciclano": "0x2"})

    result = ts4_integration.list_photos(_connection=None)

    assert result is True
    assert any("fulano" in msg and "ciclano" in msg for msg in fake_commands.output_calls)


def test_apply_photo_to_sim_noop_when_unassigned(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path)
    ts4_integration.apply_photo_to_sim(fake_sim.sim_info)
    assert fake_sim.sim_info.resend_count == 0


def test_apply_photos_to_all_sims_applies_to_each(tmp_path, monkeypatch):
    store = _use(monkeypatch, tmp_path)
    sim_a = FakeSim(sim_id=1)
    sim_b = FakeSim(sim_id=2)
    store.assign(1, PHOTO_A)
    store.assign(2, PHOTO_B)
    fake_services._manager.sims = [sim_a.sim_info, sim_b.sim_info]

    ts4_integration.apply_photos_to_all_sims()

    assert sim_a.sim_info.outfit_parts()[0] == [1001, PHOTO_A]
    assert sim_b.sim_info.outfit_parts()[0] == [1001, PHOTO_B]
