"""Installs lightweight fakes for The Sims 4's game-only modules
(`sims4`, `services`, `server_commands.argument_helpers`, `zone`,
`protocolbuffers`, `cas.cas`)
into sys.modules before any test imports photo_face_mod.ts4_integration or
photo_face_mod.hooks. The real game API is not decompiled/available here;
these fakes model the commonly documented shape of that API so the
integration layer's own logic (command dispatch, store/manifest wiring,
zone-load patching) can be exercised without the actual game.
"""
import sys
import types

import pytest


def _build_fake_sims4():
    sims4 = types.ModuleType("sims4")
    commands = types.ModuleType("sims4.commands")
    commands.output_calls = []

    class CommandType:
        Live = "Live"
        Cheat = "Cheat"
        DebugOnly = "DebugOnly"

    def Command(name, command_type=None):
        def decorator(func):
            func._command_name = name
            func._command_type = command_type
            return func

        return decorator

    def output(msg, _connection=None):
        commands.output_calls.append(msg)

    commands.Command = Command
    commands.CommandType = CommandType
    commands.output = output
    sims4.commands = commands
    sys.modules["sims4"] = sims4
    sys.modules["sims4.commands"] = commands


def _build_fake_services():
    services = types.ModuleType("services")

    class _FakeSimInfoManager:
        def __init__(self):
            self.sims = []

        def get_all(self):
            return list(self.sims)

    services._manager = _FakeSimInfoManager()
    services.sim_info_manager = lambda: services._manager
    sys.modules["services"] = services


def _build_fake_argument_helpers():
    server_commands = types.ModuleType("server_commands")
    argument_helpers = types.ModuleType("server_commands.argument_helpers")

    class OptionalTargetParam:
        def __init__(self, value=None):
            self.value = value

    argument_helpers.get_optional_target_result = None
    argument_helpers.OptionalTargetParam = OptionalTargetParam
    argument_helpers.get_optional_target = (
        lambda opt_sim, _connection=None: argument_helpers.get_optional_target_result
    )
    server_commands.argument_helpers = argument_helpers
    sys.modules["server_commands"] = server_commands
    sys.modules["server_commands.argument_helpers"] = argument_helpers


def _build_fake_zone():
    zone = types.ModuleType("zone")

    class Zone:
        def on_loading_screen_animation_finished(self, *args, **kwargs):
            return "original_result"

    zone.Zone = Zone
    sys.modules["zone"] = zone


def _build_fake_protobuffers_and_cas():
    protocolbuffers = types.ModuleType("protocolbuffers")
    s4common = types.ModuleType("protocolbuffers.S4Common_pb2")
    outfits = types.ModuleType("protocolbuffers.Outfits_pb2")
    from fakes import FakeBodyTypesList, FakeIdList

    s4common.IdList = FakeIdList
    outfits.BodyTypesList = FakeBodyTypesList
    protocolbuffers.S4Common_pb2 = s4common
    protocolbuffers.Outfits_pb2 = outfits
    sys.modules["protocolbuffers"] = protocolbuffers
    sys.modules["protocolbuffers.S4Common_pb2"] = s4common
    sys.modules["protocolbuffers.Outfits_pb2"] = outfits

    cas_pkg = types.ModuleType("cas")
    cas_mod = types.ModuleType("cas.cas")
    cas_mod.GLASSES = 11
    cas_mod.get_caspart_bodytype = lambda cas_part_id: cas_mod.GLASSES
    cas_pkg.cas = cas_mod
    sys.modules["cas"] = cas_pkg
    sys.modules["cas.cas"] = cas_mod


_build_fake_sims4()
_build_fake_services()
_build_fake_protobuffers_and_cas()
_build_fake_argument_helpers()
_build_fake_zone()


from fakes import FakeSim


@pytest.fixture
def fake_sim():
    return FakeSim(sim_id=12345)


@pytest.fixture(autouse=True)
def _reset_fakes():
    import services as fake_services_module
    import sims4.commands as fake_commands_module
    from server_commands import argument_helpers as fake_argument_helpers_module

    fake_commands_module.output_calls.clear()
    fake_argument_helpers_module.get_optional_target_result = None
    fake_services_module._manager.sims = []
    yield
