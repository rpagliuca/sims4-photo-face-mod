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
  --sim-name "Fulano" \
  --template packages/casp_template/base.package \
  --output dist/Fulano_photo.package
```

`--template` must point at a CAS Part `.package` that already contains a
shuffled DDS (DST) texture resource — that resource is replaced in place with
the converted photo, keeping its original type/group/instance so the CASP
resource's internal reference to it keeps resolving. **`packages/casp_template/base.package`
does not exist yet** (it's built separately with Sims4Studio under Wine, see
the project's main docs); see `src/syntheticTemplate.js` for a placeholder
generator used in development and tests.

The photo is center-cropped to a square (no perspective correction — that's
the point) and converted to DST5 with `@s4tk/images`.

## Tests

```bash
npm test
```

Runs `node --test` over `../tests/node/*.test.js` (Node's built-in test
runner, no extra framework). Covers: PNG cropping logic, PNG→DDS/DST
conversion (magic bytes + shuffle flag), package assembly/round-trip via
`@s4tk/models`, and the CLI end to end against a synthetic in-memory
template.

## Known TODOs

- **Real CASP template**: not committed yet; the synthetic fixture in
  `src/syntheticTemplate.js` is not a valid in-game CAS Part, only a
  DBPF-shaped stand-in for tests.
- **Per-Sim resource uniqueness**: the texture's TGI key is kept identical to
  the template's to preserve the CASP resource's internal texture reference
  (no CASP binary parser exists yet to patch that reference if remapped).
  This means two Sims' output `.package` files currently share the same
  texture/CASP instance IDs — installing more than one at once will make the
  game's override order pick only one. Revisit once the real template format
  is understood well enough to safely remap and patch that reference.
- **Standalone binary packaging**: `npm run build` is a placeholder. Wrapping
  the CLI with `pkg`/`nexe` (cross-compiled for Windows) is not implemented.
- `npm audit` reports moderate-severity issues inherited transitively from
  `@s4tk/images` (old `@jimp/*` / `file-type` versions) with no upstream fix
  available yet.
