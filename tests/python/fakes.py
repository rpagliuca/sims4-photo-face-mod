"""Shared fake game objects (FakeSim/FakeSimInfo) used by both conftest.py
(fixtures) and test modules that need to build several fake Sims by hand.

FakeSimInfo models the outfit API the mod uses (the same one S4CL uses):
save_outfits() returns a protobuf-like message whose outfits carry parallel
lists of part ids and body types; the mod writes it back to _base.outfits
and calls resend_outfits().
"""


class FakeIdList:
    def __init__(self, ids=None):
        self.ids = list(ids or [])


class FakeBodyTypesList:
    def __init__(self, body_types=None):
        self.body_types = list(body_types or [])


class FakeSavedOutfit:
    def __init__(self, category, pairs):
        self.category = category
        self.parts = FakeIdList(p for p, _ in pairs)
        self.body_types_list = FakeBodyTypesList(b for _, b in pairs)


class FakeSavedOutfits:
    def __init__(self, outfits):
        self.outfits = outfits

    def SerializeToString(self):
        return self


class FakeBase:
    outfits = None
    outfit_type_and_index = None


class FakeSimInfo:
    def __init__(self, sim_id, outfits=None):
        self.sim_id = sim_id
        # two outfits (everyday, sleep), each with a body part and real glasses
        self._outfits = outfits or [
            [(1001, 6), (2001, 11)],
            [(1002, 6)],
        ]
        self._base = FakeBase()
        self.resend_count = 0

    def save_outfits(self):
        return FakeSavedOutfits([FakeSavedOutfit(i, pairs) for i, pairs in enumerate(self._outfits)])

    def get_current_outfit(self):
        return (0, 0)

    def resend_outfits(self):
        saved = self._base.outfits
        self._outfits = [list(zip(o.parts.ids, o.body_types_list.body_types)) for o in saved.outfits]
        self.resend_count += 1

    def outfit_parts(self):
        return [[part for part, _ in pairs] for pairs in self._outfits]


class FakeSim:
    def __init__(self, sim_id, outfits=None):
        self.sim_info = FakeSimInfo(sim_id, outfits=outfits)
