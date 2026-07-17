"""In-game integration layer: wires PhotoAssignmentStore + PhotoManifest to
The Sims 4's script-mod API (console command + zone-load hook).

This module imports game-only modules (`sims4`, `services`,
`server_commands.argument_helpers`) and is exercised in tests via
lightweight fakes injected into `sys.modules` (see tests/python/conftest.py)
rather than the real game. The exact game API shapes referenced here
(module/class/method names, CAS mutation calls) follow community-documented
modding conventions and MUST be validated in-game before release; see
docs/base-de-conhecimento.html.
"""
import sims4.commands
import services
from server_commands.argument_helpers import OptionalTargetParam, get_optional_target

from photo_face_mod import constants, paths
from photo_face_mod.core import PhotoAssignmentStore
from photo_face_mod.manifest import PhotoManifest

store = PhotoAssignmentStore(paths.get_mod_data_dir())
manifest = PhotoManifest(paths.get_manifest_path())


def default_accessory_applier(sim_info, cas_part_id: int, swatch_index: int) -> None:
    """Best-effort application of the photo accessory CAS part to a Sim.

    EXPERIMENTAL / needs in-game verification: forcing an accessory CAS
    part onto a Sim's current outfit varies across community mods and game
    versions. This follows the commonly documented pattern of mutating the
    current outfit's CAS part list and refreshing appearance afterwards.
    """
    outfit_category_and_index = sim_info.get_current_outfit()
    outfit_data = sim_info.get_outfit(*outfit_category_and_index)
    parts = list(outfit_data.get_outfit_parts()) if outfit_data is not None else []
    parts = [p for p in parts if p != cas_part_id]
    parts.append(cas_part_id)
    sim_info.set_outfit_data(outfit_category_and_index, parts, swatch_index)
    sim_info.appearance_tracker.reset_appearance_modifiers()


def apply_photo_to_sim(sim_info, accessory_applier=default_accessory_applier) -> None:
    swatch_index = store.get(sim_info.sim_id)
    if swatch_index is None:
        return
    accessory_applier(sim_info, constants.PHOTO_ACCESSORY_CAS_PART_ID, swatch_index)


def apply_photos_to_all_sims(accessory_applier=default_accessory_applier) -> None:
    sim_info_manager = services.sim_info_manager()
    if sim_info_manager is None:
        return
    for sim_info in sim_info_manager.get_all():
        apply_photo_to_sim(sim_info, accessory_applier=accessory_applier)


@sims4.commands.Command('photofacemod.assign', command_type=sims4.commands.CommandType.Live)
def assign_photo(photo_key: str, opt_sim: OptionalTargetParam = None, _connection=None):
    sim = get_optional_target(opt_sim, _connection)
    if sim is None:
        sims4.commands.output('PhotoFaceMod: nenhum Sim selecionado.', _connection)
        return False
    manifest.reload()
    swatch_index = manifest.swatch_for(photo_key)
    if swatch_index is None:
        sims4.commands.output(
            'PhotoFaceMod: foto "%s" nao encontrada no manifesto.' % photo_key, _connection
        )
        return False
    store.assign(sim.sim_info.sim_id, swatch_index)
    apply_photo_to_sim(sim.sim_info)
    sims4.commands.output('PhotoFaceMod: foto "%s" atribuida.' % photo_key, _connection)
    return True


@sims4.commands.Command('photofacemod.remove', command_type=sims4.commands.CommandType.Live)
def remove_photo(opt_sim: OptionalTargetParam = None, _connection=None):
    sim = get_optional_target(opt_sim, _connection)
    if sim is None:
        sims4.commands.output('PhotoFaceMod: nenhum Sim selecionado.', _connection)
        return False
    removed = store.remove(sim.sim_info.sim_id)
    sims4.commands.output(
        'PhotoFaceMod: foto removida.' if removed else 'PhotoFaceMod: este Sim nao tinha foto atribuida.',
        _connection,
    )
    return True


@sims4.commands.Command('photofacemod.list', command_type=sims4.commands.CommandType.Live)
def list_photos(_connection=None):
    keys = manifest.photo_keys()
    sims4.commands.output(
        'PhotoFaceMod: fotos disponiveis: %s' % (', '.join(keys) or '(nenhuma)'), _connection
    )
    return True
