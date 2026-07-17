import zone_spin_up
from fakes import FakeSim

from photo_face_mod import hooks, ts4_integration
from photo_face_mod.core import PhotoAssignmentStore


def test_install_wraps_load_and_calls_original(monkeypatch):
    hooks.install()
    zone = zone_spin_up.ZoneSpinUp()
    result = zone.load()
    assert result == "original_load_result"


def test_install_is_idempotent():
    hooks.install()
    first_load = zone_spin_up.ZoneSpinUp.load
    hooks.install()
    assert zone_spin_up.ZoneSpinUp.load is first_load


def test_installed_hook_applies_photos_to_all_sims(tmp_path, monkeypatch):
    import services as fake_services

    store = PhotoAssignmentStore(tmp_path / "data")
    sim = FakeSim(sim_id=42)
    store.assign(42, 1)
    monkeypatch.setattr(ts4_integration, "store", store)
    fake_services._manager.sims = [sim.sim_info]

    hooks.install()
    zone_spin_up.ZoneSpinUp().load()

    assert sim.sim_info.set_outfit_data_calls
