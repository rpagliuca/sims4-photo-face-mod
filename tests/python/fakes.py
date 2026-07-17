"""Shared fake game objects (FakeSim/FakeSimInfo) used by both conftest.py
(fixtures) and test modules that need to build several fake Sims by hand.
"""


class FakeOutfitData:
    def __init__(self, parts=None):
        self._parts = list(parts or [])

    def get_outfit_parts(self):
        return list(self._parts)


class FakeSimInfo:
    def __init__(self, sim_id, outfit_parts=None):
        self.sim_id = sim_id
        self._outfit = ("Everyday", 0)
        self._outfit_data = FakeOutfitData(outfit_parts)
        self.set_outfit_data_calls = []
        self.appearance_refreshed = 0

    def get_current_outfit(self):
        return self._outfit

    def get_outfit(self, category, index):
        return self._outfit_data

    def set_outfit_data(self, outfit_category_and_index, parts, swatch_index):
        self.set_outfit_data_calls.append((outfit_category_and_index, list(parts), swatch_index))
        self._outfit_data = FakeOutfitData(parts)

    @property
    def appearance_tracker(self):
        return self

    def reset_appearance_modifiers(self):
        self.appearance_refreshed += 1


class FakeSim:
    def __init__(self, sim_id, outfit_parts=None):
        self.sim_info = FakeSimInfo(sim_id, outfit_parts=outfit_parts)
