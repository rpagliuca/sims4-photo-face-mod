# Companion tool

Node.js CLI that turns a user's PNG photo into its own CAS part (a clone of
the plate in `packages/casp_template/base.package` with the photo as
texture), accumulated in a single `.package` (DBPF). Built on
[Sims4Toolkit](https://sims4toolkit.com/) (`@s4tk/models`, `@s4tk/images`,
`@s4tk/hashing`).

## Install

```bash
cd companion
npm install
```

## Usage

```bash
node src/index.js assign \
  --photo foto.png \
  --photo-key fulano \
  --manifest "Mods/PhotoFaceMod/photo_manifest.json" \
  --template ../packages/casp_template/base.package \
  --output "Mods/PhotoFaceMod/photofacemod.package"
```

Run it once per photo. Each `--photo-key` (the string typed in-game as
`photofacemod.assign <photo_key>`) becomes its own CASP; re-running with the
same key replaces that photo in place, since the CASP and texture instances
are derived from the key (`fnv64`).

- `--template`: `packages/casp_template/base.package`, cloned on the first run.
- `--output`: the single accumulated `.package` the player installs. **If it
  already exists, it is used as the base instead of `--template`**, so photos
  accumulate.
- `--manifest`: `photo_manifest.json`, `photo_key -> "0x<CASP instance>"`,
  read at runtime by the Python mod's `PhotoManifest`. It must sit at
  `Mods/PhotoFaceMod/photo_manifest.json` (see
  `src/photo_face_mod/paths.py`). The manifest also tells the tool which CASPs
  in an accumulated package it generated, so keep it next to the package.
- `--sim-name`: optional, logging only.

## What happens to the photo

1. Center-cropped to the plate's aspect (22 x 28 cm) and squeezed into the
   256 x 128 glasses rectangle (x 512..768, y 128..256) of a transparent
   1024 x 2048 atlas, the texture layout the game composes for each Sim.
   No perspective correction: that's the point.
2. Compressed to DXT5 with mips (`@s4tk/images`) and run-length encoded as
   RLE2 (`src/rle2.js`, ported from s4pi), the format Sims4Studio writes for
   CAS diffuse textures.
3. The template CASP is copied and only its diffuse TGI is rewritten to point
   at the new texture; meshes and region map stay shared.

## Tests

```bash
npm test
```

Uses Node's built-in test runner against the real `base.package`. Covers the
RLE2 round trip (byte-identical to Sims4Studio's output), the atlas layout,
CASP cloning, accumulation and replacement, and the CLI.
