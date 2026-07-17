"""Patches the game's zone-load lifecycle to reapply photo accessories to
every Sim whenever a save loads. Uses the "wrap and call original" idiom
common to TS4 script mods (no dependency on S4CL). The exact hook point
(`zone_spin_up.ZoneSpinUp.load`) follows community-documented conventions
and must be verified in-game; see docs/base-de-conhecimento.html.
"""
from photo_face_mod.ts4_integration import apply_photos_to_all_sims

_PATCHED_ATTR = "_photo_face_mod_patched"


def install() -> None:
    import zone_spin_up

    zone_spin_up_class = zone_spin_up.ZoneSpinUp
    if getattr(zone_spin_up_class, _PATCHED_ATTR, False):
        return

    original_load = zone_spin_up_class.load

    def patched_load(self, *args, **kwargs):
        result = original_load(self, *args, **kwargs)
        apply_photos_to_all_sims()
        return result

    zone_spin_up_class.load = patched_load
    setattr(zone_spin_up_class, _PATCHED_ATTR, True)
