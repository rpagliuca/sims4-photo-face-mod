"""Top-level module bootstrapped by the game when it imports the
.ts4script archive. Importing ts4_integration registers the console
commands. Kept separate from the photo_face_mod package so the package
stays importable in tests without the game loader.
"""
from photo_face_mod import ts4_integration  # noqa: F401
