"""In-game integration layer: console commands that put a face (a photo CAS
part from the manifests) on the selected Sim, swap it or take it off.

There is no separate persistence: the commands edit the Sim's outfits and
the game saves outfits with the save file, exactly like a choice made in
Create-a-Sim. That is also why a face picked or removed in CAS sticks: the
mod never reapplies anything on load (validated in game 1.128.90).

This module imports game-only modules (`sims4`, `server_commands`,
`protocolbuffers`, `cas`) and is exercised in tests via fakes injected into
`sys.modules` (see tests/python/conftest.py).
"""
import sims4.commands
from server_commands.argument_helpers import OptionalTargetParam, get_optional_target

from photo_face_mod import paths
from photo_face_mod.manifest import PhotoManifest

manifest = PhotoManifest(paths.get_mod_dir())


def _rewrite_outfits(sim_info, edit_parts) -> None:
    """Rewrites the part list of every outfit of a Sim and pushes it to the game.

    Same pattern as S4CL's CommonSimOutfitIO: serialize the outfits with
    save_outfits(), edit each outfit's parallel lists of part ids and body
    types, store them back in sim_info._base.outfits and resend. Every outfit
    is edited so the face survives changing clothes.

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


def current_face(sim_info):
    """photo_key of the face on the Sim's current outfit, or None."""
    known = manifest.cas_part_ids()
    saved = sim_info.save_outfits()
    category, index = sim_info.get_current_outfit()
    for outfit in saved.outfits:
        if (outfit.category, getattr(outfit, "outfit_index", 0)) != (category, index):
            continue
        for part in outfit.parts.ids:
            if part in known:
                return known[part]
    for outfit in saved.outfits:
        for part in outfit.parts.ids:
            if part in known:
                return known[part]
    return None


def put_face(sim_info, cas_part_id: int) -> None:
    """Puts the face on every outfit, replacing whatever was in its body-type
    slot (the faces are glasses, so: glasses) and any other face."""
    from cas.cas import get_caspart_bodytype

    body_type = int(get_caspart_bodytype(cas_part_id))
    known = set(manifest.cas_part_ids())

    def edit(pairs):
        kept = [(part, bt) for part, bt in pairs if int(bt) != body_type and part not in known]
        return kept + [(cas_part_id, body_type)]

    _rewrite_outfits(sim_info, edit)


def take_face_off(sim_info) -> bool:
    """Takes every known face off every outfit. Returns False if there was none."""
    known = set(manifest.cas_part_ids())
    found = []

    def edit(pairs):
        found.extend(part for part, _ in pairs if part in known)
        return [(part, bt) for part, bt in pairs if part not in known]

    _rewrite_outfits(sim_info, edit)
    return bool(found)


def _target(opt_sim, _connection):
    sim = get_optional_target(opt_sim, _connection)
    if sim is None:
        sims4.commands.output('PhotoFaceMod: nenhum Sim selecionado.', _connection)
    return sim


@sims4.commands.Command('photofacemod.assign', command_type=sims4.commands.CommandType.Live)
def assign_photo(photo_key: str, opt_sim: OptionalTargetParam = None, _connection=None):
    sim = _target(opt_sim, _connection)
    if sim is None:
        return False
    manifest.reload()
    cas_part_id = manifest.cas_part_for(photo_key)
    if cas_part_id is None:
        sims4.commands.output('PhotoFaceMod: cara "%s" nao encontrada.' % photo_key, _connection)
        return False
    put_face(sim.sim_info, cas_part_id)
    sims4.commands.output('PhotoFaceMod: cara "%s" atribuida.' % photo_key, _connection)
    return True


@sims4.commands.Command('photofacemod.next', command_type=sims4.commands.CommandType.Live)
def next_photo(opt_sim: OptionalTargetParam = None, _connection=None):
    """Swaps to the next face in alphabetical order (the first one if the Sim has none)."""
    sim = _target(opt_sim, _connection)
    if sim is None:
        return False
    manifest.reload()
    keys = manifest.photo_keys()
    if not keys:
        sims4.commands.output('PhotoFaceMod: nenhuma cara instalada.', _connection)
        return False
    current = current_face(sim.sim_info)
    key = keys[(keys.index(current) + 1) % len(keys)] if current in keys else keys[0]
    put_face(sim.sim_info, manifest.cas_part_for(key))
    sims4.commands.output('PhotoFaceMod: cara "%s".' % key, _connection)
    return True


@sims4.commands.Command('photofacemod.remove', command_type=sims4.commands.CommandType.Live)
def remove_photo(opt_sim: OptionalTargetParam = None, _connection=None):
    sim = _target(opt_sim, _connection)
    if sim is None:
        return False
    manifest.reload()
    removed = take_face_off(sim.sim_info)
    sims4.commands.output(
        'PhotoFaceMod: cara removida.' if removed else 'PhotoFaceMod: este Sim nao tinha cara.',
        _connection,
    )
    return True


@sims4.commands.Command('photofacemod.list', command_type=sims4.commands.CommandType.Live)
def list_photos(_connection=None):
    manifest.reload()
    keys = manifest.photo_keys()
    sims4.commands.output('PhotoFaceMod: caras: %s' % (', '.join(keys) or '(nenhuma)'), _connection)
    return True
