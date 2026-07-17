#!/usr/bin/env python3
"""Builds the .ts4script artifact: compiles src/ to .pyc and zips it.

The Sims 4 embeds CPython 3.7 and only loads .pyc bytecode from
.ts4script archives (plain .py alone is silently ignored by the game).
CPython bytecode is not officially cross-compilable between versions, so
this script should be run with an actual Python 3.7 interpreter for a
build that is guaranteed compatible with the game. If 3.7 isn't
available, it falls back to whatever interpreter runs it and prints a
loud warning -- see docs/compilacao.html.
"""
import argparse
import py_compile
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
MOD_PACKAGE_DIR = SRC_DIR / "photo_face_mod"
ENTRYPOINT_FILE = SRC_DIR / "mod_entrypoint.py"
DEFAULT_OUTPUT = REPO_ROOT / "build" / "dist" / "photofacemod.ts4script"


def check_python_version() -> None:
    if sys.version_info[:2] != (3, 7):
        print(
            "AVISO: rodando com Python %d.%d, nao 3.7. O TS4 embute CPython "
            "3.7 e o bytecode .pyc gerado pode ser incompativel com o jogo. "
            "Rode este script com um interpretador 3.7 real "
            "(ex: `python3.7 build/build_ts4script.py`) para um build confiavel."
            % (sys.version_info.major, sys.version_info.minor),
            file=sys.stderr,
        )


def _compile_to_pyc(py_file: Path) -> Path:
    pyc_path = py_file.with_suffix(".pyc")
    py_compile.compile(str(py_file), cfile=str(pyc_path), doraise=True)
    return pyc_path


def build(output_path: Path) -> Path:
    check_python_version()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    py_files = [ENTRYPOINT_FILE, *sorted(MOD_PACKAGE_DIR.rglob("*.py"))]
    compiled = []
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for py_file in py_files:
                pyc_path = _compile_to_pyc(py_file)
                compiled.append(pyc_path)
                arcname = pyc_path.relative_to(SRC_DIR)
                zf.write(pyc_path, arcname=str(arcname))
    finally:
        # NOTE: Path.unlink(missing_ok=...) is Python 3.8+; this script must
        # also run correctly under the target Python 3.7, hence the try/except.
        for pyc_path in compiled:
            try:
                pyc_path.unlink()
            except FileNotFoundError:
                pass

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    result = build(Path(args.output))
    print("Built %s" % result)


if __name__ == "__main__":
    main()
