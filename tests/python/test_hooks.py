import sys

import zone
from fakes import FakeSim

from photo_face_mod import hooks, ts4_integration
from photo_face_mod.core import PhotoAssignmentStore


def test_install_wraps_the_hook_and_calls_original():
    assert hooks.install() is True
    assert zone.Zone().on_loading_screen_animation_finished() == "original_result"


def test_install_is_idempotent():
    hooks.install()
    first = zone.Zone.on_loading_screen_animation_finished
    hooks.install()
    assert zone.Zone.on_loading_screen_animation_finished is first


def test_installed_hook_applies_photos_to_all_sims(tmp_path, monkeypatch):
    import services as fake_services

    store = PhotoAssignmentStore(tmp_path / "data")
    sim = FakeSim(sim_id=42)
    store.assign(42, 1)
    monkeypatch.setattr(ts4_integration, "store", store)
    fake_services._manager.sims = [sim.sim_info]

    hooks.install()
    zone.Zone().on_loading_screen_animation_finished()

    assert sim.sim_info.resend_count == 1


def test_a_failing_apply_does_not_break_the_load(monkeypatch):
    def boom():
        raise RuntimeError("x")

    monkeypatch.setattr(hooks, "apply_photos_to_all_sims", boom)
    monkeypatch.delattr(zone.Zone, hooks._PATCHED_ATTR, raising=False)
    original = zone.Zone.on_loading_screen_animation_finished
    try:
        hooks.install()
        assert zone.Zone().on_loading_screen_animation_finished() == "original_result"
    finally:
        zone.Zone.on_loading_screen_animation_finished = original


def test_install_returns_false_when_the_game_module_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "zone", None)
    assert hooks.install() is False
