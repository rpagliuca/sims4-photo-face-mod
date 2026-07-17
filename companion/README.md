# Companion tool

Node.js CLI that turns a user's PNG photo into the CAS Part texture of a
`.package` (DBPF) file, for the tosco 2D photo-face accessory. Built on
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
  --photo-key rafael \
  --manifest "Mods/PhotoFaceMod/photo_manifest.json" \
  --template packages/casp_template/base.package \
  --output "Mods/PhotoFaceMod/photofacemod.package" \
  --sim-name "Rafael"
```

Run this once per Sim/photo you want to register; each Sim gets a distinct
`--photo-key` (the same string the player later types in-game as
`photofacemod.assign <photo_key>`). Re-running with an existing `--photo-key`
updates that Sim's photo without allocating a new swatch.

- `--template` must point at a CAS Part `.package` with **N pre-made swatches**
  (N separate DstImage/shuffled-DDS texture resources, each already wired up
  internally by the CASP resource — that's what Sims4Studio does when the
  swatches are created; see `packages/casp_template/README.md`).
- `--output` is the single accumulated `.package` file the player installs.
  **If it already exists, it is used as the base instead of `--template`** —
  so the first `assign` for a given `--output` clones the template, and every
  later `assign` (a different Sim, normally) adds to that same file instead
  of starting over and losing previously-assigned Sims. Ship this one file.
- `--manifest` is `photo_manifest.json` (`photo_key -> swatch_index`), read at
  runtime by the Python mod's `PhotoManifest`
  (`src/photo_face_mod/manifest.py`) to resolve `photofacemod.assign
  <photo_key>`. It must sit at the exact path
  `Mods/PhotoFaceMod/photo_manifest.json` under the game's user data folder
  — see `src/photo_face_mod/paths.py::get_manifest_path()` (note:
  `MODS_FOLDER_NAME = "PhotoFaceMod"` there is the player-facing Mods/
  subfolder; `MOD_NAME = "photo_face_mod"` is only used for the separate
  `mod_data/` persistence folder, not this manifest path). Created
  automatically if it doesn't exist yet.
- `--sim-name` is optional, logging-only, and does **not** affect which
  resource is touched — `--photo-key` (via the manifest) is what determines
  the swatch, on purpose: this is what lets two Sims coexist in the same
  Mods folder without clobbering each other's texture (see the "no
  collision" and "accumulates both Sims'" tests in `tests/node/`).
- `--swatch-index` is an optional escape hatch to force a specific index
  instead of letting the manifest allocate/reuse one; normal use shouldn't
  need it.

**`packages/casp_template/base.package` does not exist yet** (it's built
separately with Sims4Studio under Wine, see the project's main docs); see
`src/syntheticTemplate.js` for a placeholder generator (with multiple
swatches) used in development and tests.

The photo is center-cropped to a square (no perspective correction — that's
the point) and converted to DST5 with `@s4tk/images`.

### How photo_key/swatch_index maps to a resource key

`companion/src/manifest.js` owns `photo_key -> swatch_index` (JSON, persisted
in `photo_manifest.json`, the same file the Python mod reads). Separately,
`findTextureEntryForSwatch` (in `packageBuilder.js`) maps `swatch_index` to an
actual `DstImage` resource by sorting all of the template's DstImage entries
by (group, instance) and indexing into that sorted list. This second mapping
is a functional fallback, not a guarantee tied to how Sims4Studio orders
swatches internally. The robust fix — an explicit `template_manifest.json`
(swatch_index -> {type, group, instance}) emitted alongside `base.package`
when it's built — is a TODO tracked in `packages/casp_template/README.md`,
since it depends on how that template is actually produced.

## Tests

```bash
npm test
```

Runs `node --test` over `../tests/node/*.test.js` (Node's built-in test
runner, no extra framework). Covers: PNG cropping logic, PNG→DDS/DST
conversion (magic bytes + shuffle flag), package assembly/round-trip via
`@s4tk/models`, `photo_manifest.json` allocation/reuse logic, and the CLI end
to end against a synthetic in-memory template — including running `assign`
twice for the same `--output` and confirming both Sims' textures survive in
the one accumulated `.package`.

## Known TODOs

- **Real CASP template**: not committed yet; the synthetic fixture in
  `src/syntheticTemplate.js` is not a valid in-game CAS Part, only a
  DBPF-shaped stand-in for tests.
- **swatch_index -> resource key mapping**: currently positional (sorted
  DstImage entries by group/instance), not backed by an explicit manifest.
  Fine as long as `base.package` isn't regenerated with swatches reordered;
  a `template_manifest.json` would remove that assumption (see above).
- **Accumulated package still holds every swatch, always**: each `assign`
  writes out the full package (all N swatch slots), whether or not all of
  them are assigned yet - harmless (one file either way), just not minimal.
- **Standalone binary packaging**: `npm run build` is a placeholder. Wrapping
  the CLI with `pkg`/`nexe` (cross-compiled for Windows) is not implemented.
- `npm audit` reports moderate-severity issues inherited transitively from
  `@s4tk/images` (old `@jimp/*` / `file-type` versions) with no upstream fix
  available yet.
