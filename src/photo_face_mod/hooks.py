"""Patches the game's zone-load lifecycle to reapply photo accessories to
every Sim whenever a lot finishes loading. Uses the "wrap and call original"
idiom common to TS4 script mods (no dependency on S4CL), on
`zone.Zone.on_loading_screen_animation_finished`, the same hook point S4CL
uses for its "zone load end" event.

`zone_spin_up.ZoneSpinUp.load`, the hook point used before, does not exist
in the game (verified on 1.128.90: ModuleNotFoundError at import, see
docs/base-de-conhecimento.html). A hook failure must never take the console
commands down with it, so install() logs and carries on.
"""
from photo_face_mod.ts4_integration import apply_photos_to_all_sims

_PATCHED_ATTR = "_photo_face_mod_patched"


def install() -> bool:
    try:
        import zone

        zone_class = zone.Zone
    except Exception:  # noqa: BLE001 - never break the mod's import
        return False
    if getattr(zone_class, _PATCHED_ATTR, False):
        return True

    original = zone_class.on_loading_screen_animation_finished

    def patched(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        try:
            apply_photos_to_all_sims()
        except Exception:  # noqa: BLE001 - a photo failure must not break the load
            pass
        return result

    zone_class.on_loading_screen_animation_finished = patched
    setattr(zone_class, _PATCHED_ATTR, True)
    return True
