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

from photo_face_mod import paths
from photo_face_mod.core import PhotoAssignmentStore
from photo_face_mod.manifest import PhotoManifest

store = PhotoAssignmentStore(paths.get_mod_data_dir())
manifest = PhotoManifest(paths.get_manifest_path())


def _rewrite_outfits(sim_info, edit_parts) -> None:
    """Rewrites the part list of every outfit of a Sim and pushes it to the game.

    EXPERIMENTAL / needs in-game verification. Follows the pattern community
    mods use (S4CL's CommonSimOutfitIO): serialize the outfits with
    save_outfits(), edit each outfit's parallel lists of part ids and body
    types, store them back in sim_info._base.outfits and resend. Every
    outfit is edited so the photo survives changing clothes.

    edit_parts(pairs) receives and returns a list of (part_id, body_type).
    """
    from protocolbuffers import Outfits_pb2, S4Common_pb2

    saved = sim_info.save_outfits()
    for outfit in saved.outfits:
        pairs = list(zip(outfit.parts.ids, outfit.body_types_list.body_types))
        pairs = edit_parts(pairs)
        outfit.parts = S4Common_pb2.IdList()
        outfit.parts.ids.extend(part for part, _ in pairs)
        outfit.body_types_list = Outfits_pb2.BodyTypesList()
        outfit.body_types_list.body_types.extend(body_type for _, body_type in pairs)
    sim_info._base.outfits = saved.SerializeToString()
    sim_info._base.outfit_type_and_index = sim_info.get_current_outfit()
    sim_info.resend_outfits()


def default_accessory_applier(sim_info, cas_part_id: int) -> None:
    """Puts the photo CAS part on every outfit, replacing whatever was in its
    body-type slot (the template is a pair of glasses, so: glasses)."""
    from cas.cas import get_caspart_bodytype

    body_type = int(get_caspart_bodytype(cas_part_id))

    def edit(pairs):
        kept = [(part, bt) for part, bt in pairs if int(bt) != body_type]
        return kept + [(cas_part_id, body_type)]

    _rewrite_outfits(sim_info, edit)


def default_accessory_remover(sim_info, cas_part_id: int) -> None:
    """Takes the photo CAS part off every outfit."""
    _rewrite_outfits(sim_info, lambda pairs: [(part, bt) for part, bt in pairs if part != cas_part_id])


def apply_photo_to_sim(sim_info, accessory_applier=default_accessory_applier) -> None:
    cas_part_id = store.get(sim_info.sim_id)
    if cas_part_id is None:
        return
    accessory_applier(sim_info, cas_part_id)


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
    cas_part_id = manifest.cas_part_for(photo_key)
    if cas_part_id is None:
        sims4.commands.output(
            'PhotoFaceMod: foto "%s" nao encontrada no manifesto.' % photo_key, _connection
        )
        return False
    previous = store.get(sim.sim_info.sim_id)
    if previous is not None and previous != cas_part_id:
        default_accessory_remover(sim.sim_info, previous)
    store.assign(sim.sim_info.sim_id, cas_part_id)
    apply_photo_to_sim(sim.sim_info)
    sims4.commands.output('PhotoFaceMod: foto "%s" atribuida.' % photo_key, _connection)
    return True


@sims4.commands.Command('photofacemod.remove', command_type=sims4.commands.CommandType.Live)
def remove_photo(opt_sim: OptionalTargetParam = None, _connection=None):
    sim = get_optional_target(opt_sim, _connection)
    if sim is None:
        sims4.commands.output('PhotoFaceMod: nenhum Sim selecionado.', _connection)
        return False
    cas_part_id = store.get(sim.sim_info.sim_id)
    removed = store.remove(sim.sim_info.sim_id)
    if cas_part_id is not None:
        default_accessory_remover(sim.sim_info, cas_part_id)
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
