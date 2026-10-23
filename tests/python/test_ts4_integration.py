import json

import sims4.commands as fake_commands
from server_commands import argument_helpers as fake_argument_helpers

from fakes import FakeSim
from photo_face_mod import ts4_integration
from photo_face_mod.manifest import PhotoManifest

PIRATA = 0x9D09F8AE8D0CEC54
ROBO = 0x8000000000000002
FOTO = 0x8000000000000003
GLASSES = 11


def _use(monkeypatch, tmp_path, pack=None, own=None):
    """Mod folder with the bundled pack manifest and the player's own one."""
    if pack is not None:
        (tmp_path / "photo_manifest_papelao.json").write_text(json.dumps(pack), encoding="utf-8")
    if own is not None:
        (tmp_path / "photo_manifest.json").write_text(json.dumps(own), encoding="utf-8")
    monkeypatch.setattr(ts4_integration, "manifest", PhotoManifest(tmp_path))


def _hex(value):
    return "0x%016X" % value


def _select(sim):
    fake_argument_helpers.get_optional_target_result = sim


def test_commands_need_a_selected_sim():
    _select(None)
    assert ts4_integration.assign_photo("pirata", None, _connection=None) is False
    assert ts4_integration.next_photo(None, _connection=None) is False
    assert ts4_integration.remove_photo(None, _connection=None) is False
    assert any("nenhum Sim selecionado" in msg for msg in fake_commands.output_calls)


def test_assign_unknown_key_reports_error(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"pirata": _hex(PIRATA)})
    _select(fake_sim)
    assert ts4_integration.assign_photo("desconhecido", None, _connection=None) is False
    assert any("nao encontrada" in msg for msg in fake_commands.output_calls)


def test_assign_puts_the_face_on_every_outfit_replacing_glasses(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"pirata": _hex(PIRATA)})
    _select(fake_sim)

    assert ts4_integration.assign_photo("pirata", None, _connection=None) is True

    assert fake_sim.sim_info.outfit_parts() == [[1001, PIRATA], [1002, PIRATA]]
    assert fake_sim.sim_info._outfits[0][1] == (PIRATA, GLASSES)
    assert fake_sim.sim_info.resend_count == 1


def test_faces_from_the_pack_and_from_own_photos_are_both_available(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"pirata": _hex(PIRATA)}, own={"foto": _hex(FOTO)})
    _select(fake_sim)
    ts4_integration.assign_photo("foto", None, _connection=None)
    assert fake_sim.sim_info.outfit_parts()[0] == [1001, FOTO]
    ts4_integration.list_photos(_connection=None)
    assert any("foto" in msg and "pirata" in msg for msg in fake_commands.output_calls)


def test_assigning_another_face_swaps_it(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"pirata": _hex(PIRATA), "robo": _hex(ROBO)})
    _select(fake_sim)
    ts4_integration.assign_photo("pirata", None, _connection=None)
    ts4_integration.assign_photo("robo", None, _connection=None)
    assert fake_sim.sim_info.outfit_parts() == [[1001, ROBO], [1002, ROBO]]


def test_next_cycles_alphabetically_and_wraps(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"robo": _hex(ROBO), "pirata": _hex(PIRATA)})
    _select(fake_sim)

    ts4_integration.next_photo(None, _connection=None)
    assert ts4_integration.current_face(fake_sim.sim_info) == "pirata"
    ts4_integration.next_photo(None, _connection=None)
    assert ts4_integration.current_face(fake_sim.sim_info) == "robo"
    ts4_integration.next_photo(None, _connection=None)
    assert ts4_integration.current_face(fake_sim.sim_info) == "pirata"


def test_next_with_no_faces_installed(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path)
    _select(fake_sim)
    assert ts4_integration.next_photo(None, _connection=None) is False


def test_remove_takes_the_face_off(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"pirata": _hex(PIRATA)})
    _select(fake_sim)
    ts4_integration.assign_photo("pirata", None, _connection=None)

    assert ts4_integration.remove_photo(None, _connection=None) is True

    assert fake_sim.sim_info.outfit_parts() == [[1001], [1002]]
    assert ts4_integration.current_face(fake_sim.sim_info) is None
    assert any("removida" in msg for msg in fake_commands.output_calls)


def test_remove_when_the_sim_has_no_face(tmp_path, monkeypatch, fake_sim):
    _use(monkeypatch, tmp_path, pack={"pirata": _hex(PIRATA)})
    _select(fake_sim)
    ts4_integration.remove_photo(None, _connection=None)
    assert fake_sim.sim_info.outfit_parts() == [[1001, 2001], [1002]], "real glasses stay"
    assert any("nao tinha cara" in msg for msg in fake_commands.output_calls)
