"""Top-level module bootstrapped by the game when it imports the
.ts4script archive. Kept slim and separate from the photo_face_mod
package so the package itself stays importable in tests without the game
loader's import-everything-at-root behavior being required.
"""
from photo_face_mod import hooks

hooks.install()
