import json

import sims4.commands as fake_commands
import services as fake_services
from server_commands import argument_helpers as fake_argument_helpers

from fakes import FakeSim
from photo_face_mod import ts4_integration
from photo_face_mod.core import PhotoAssignmentStore
from photo_face_mod.manifest import PhotoManifest


def _write_manifest(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_assign_photo_with_no_sim_selected_reports_error():
    fake_argument_helpers.get_optional_target_result = None
    result = ts4_integration.assign_photo("rafael", None, _connection=None)
    assert result is False
    assert any("nenhum Sim selecionado" in msg for msg in fake_commands.output_calls)


def test_assign_photo_unknown_key_reports_error(tmp_path, monkeypatch, fake_sim):
    fake_argument_helpers.get_optional_target_result = fake_sim
    monkeypatch.setattr(ts4_integration, "manifest", PhotoManifest(tmp_path / "manifest.json"))
    result = ts4_integration.assign_photo("desconhecido", None, _connection=None)
    assert result is False
    assert any("nao encontrada" in msg for msg in fake_commands.output_calls)


def test_assign_photo_success_persists_and_applies(tmp_path, monkeypatch, fake_sim):
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, {"rafael": 2})
    monkeypatch.setattr(ts4_integration, "manifest", PhotoManifest(manifest_path))
    monkeypatch.setattr(ts4_integration, "store", PhotoAssignmentStore(tmp_path / "data"))
    fake_argument_helpers.get_optional_target_result = fake_sim

    result = ts4_integration.assign_photo("rafael", None, _connection=None)

    assert result is True
    assert ts4_integration.store.get(fake_sim.sim_info.sim_id) == 2
    assert fake_sim.sim_info.set_outfit_data_calls
    assert fake_sim.sim_info.appearance_refreshed == 1
    assert any("atribuida" in msg for msg in fake_commands.output_calls)


def test_remove_photo_existing(tmp_path, monkeypatch, fake_sim):
    store = PhotoAssignmentStore(tmp_path / "data")
    store.assign(fake_sim.sim_info.sim_id, 1)
    monkeypatch.setattr(ts4_integration, "store", store)
    fake_argument_helpers.get_optional_target_result = fake_sim

    result = ts4_integration.remove_photo(None, _connection=None)

    assert result is True
    assert store.get(fake_sim.sim_info.sim_id) is None
    assert any("removida" in msg for msg in fake_commands.output_calls)


def test_remove_photo_when_none_assigned(tmp_path, monkeypatch, fake_sim):
    monkeypatch.setattr(ts4_integration, "store", PhotoAssignmentStore(tmp_path / "data"))
    fake_argument_helpers.get_optional_target_result = fake_sim

    result = ts4_integration.remove_photo(None, _connection=None)

    assert result is True
    assert any("nao tinha foto" in msg for msg in fake_commands.output_calls)


def test_list_photos_outputs_available_keys(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, {"rafael": 0, "irmao": 1})
    monkeypatch.setattr(ts4_integration, "manifest", PhotoManifest(manifest_path))

    result = ts4_integration.list_photos(_connection=None)

    assert result is True
    assert any("rafael" in msg and "irmao" in msg for msg in fake_commands.output_calls)


def test_apply_photo_to_sim_noop_when_unassigned(tmp_path, monkeypatch, fake_sim):
    monkeypatch.setattr(ts4_integration, "store", PhotoAssignmentStore(tmp_path / "data"))
    ts4_integration.apply_photo_to_sim(fake_sim.sim_info)
    assert fake_sim.sim_info.set_outfit_data_calls == []


def test_apply_photos_to_all_sims_applies_to_each(tmp_path, monkeypatch):
    store = PhotoAssignmentStore(tmp_path / "data")
    sim_a = FakeSim(sim_id=1)
    sim_b = FakeSim(sim_id=2)
    store.assign(1, 0)
    store.assign(2, 3)
    monkeypatch.setattr(ts4_integration, "store", store)
    fake_services._manager.sims = [sim_a.sim_info, sim_b.sim_info]

    ts4_integration.apply_photos_to_all_sims()

    assert sim_a.sim_info.set_outfit_data_calls
    assert sim_b.sim_info.set_outfit_data_calls
    assert sim_b.sim_info.set_outfit_data_calls[0][2] == 3
