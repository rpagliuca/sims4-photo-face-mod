#!/usr/bin/env python3
"""Attempts to drive Sims4Studio (running under Wine + Xvfb) to produce
packages/casp_template/base.package automatically.

HONEST STATUS: the click/keyboard sequence below is NOT implemented. Doing
so requires iterating against the real Sims4Studio window (via `xdotool`/
`wmctrl`, watched over VNC or a recorded X11 session) to find the actual
control positions and dialog flow -- something that can't be produced
correctly by guessing coordinates, and this environment has no access to
Windows/Wine/Sims4Studio/the game to verify against. See
packages/casp_template/README.md for the recommended manual fallback (the
Rafael creates base.package once on Windows and commits it) and for how to
finish this automation later if still desired.

This script is intentionally a stub that fails loudly and immediately
rather than pretending to succeed, so CI failures here are always
`continue-on-error` in .github/workflows/ci.yml and never block the rest
of the build.
"""
import sys


def main() -> int:
    print(
        "automate_casp.py: automacao de UI do Sims4Studio ainda nao "
        "implementada -- ver packages/casp_template/README.md para o "
        "fallback manual recomendado.",
        file=sys.stderr,
    )
    raise NotImplementedError(
        "UI automation for Sims4Studio requires iterating against the real "
        "app (xdotool click/key sequence discovery), which this environment "
        "cannot do. See packages/casp_template/README.md."
    )


if __name__ == "__main__":
    sys.exit(main())
