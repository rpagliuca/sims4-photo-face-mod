"use strict";

const fs = require("node:fs");
const path = require("node:path");

const { Package } = require("@s4tk/models");
const { BinaryResourceType } = require("@s4tk/models/enums");

const { pngBufferToTextureResource } = require("./texture");

/**
 * Reads a .package file from disk and parses it as a DBPF Package.
 *
 * @param {string} templatePath Path to the template .package file.
 * @returns {import("@s4tk/models").Package}
 */
function loadTemplatePackage(templatePath) {
  const buffer = fs.readFileSync(templatePath);
  return Package.from(buffer);
}

/**
 * Returns every DstImage (shuffled DDS) resource entry in the template,
 * i.e. one per CAS swatch, in a deterministic order (sorted by group then
 * instance - NOT file/physical order, which S4TK/DBPF does not guarantee is
 * stable across re-saves).
 *
 * This ordering is a fallback: the robust way to map a swatch_index to a
 * resource key is an explicit manifest emitted by whatever builds
 * base.package (TODO: have the Sims4Studio/Wine template build also emit a
 * template_manifest.json with `swatch_index -> {type, group, instance}`,
 * see packages/casp_template/README.md). Until that exists, "swatch N is the
 * N-th DstImage resource by sorted key" is what we've got, and it is stable
 * as long as the template itself isn't regenerated with swatches reordered.
 *
 * @param {import("@s4tk/models").Package} pkg
 * @returns {import("@s4tk/models").ResourceEntry[]}
 */
function listTextureEntriesSorted(pkg) {
  return pkg.entries
    .filter((e) => e.key.type === BinaryResourceType.DstImage)
    .sort((a, b) => {
      if (a.key.group !== b.key.group) return a.key.group - b.key.group;
      if (a.key.instance < b.key.instance) return -1;
      if (a.key.instance > b.key.instance) return 1;
      return 0;
    });
}

/**
 * Finds the CAS Part texture resource entry (a shuffled DST image) for a
 * specific swatch index inside a template package. This is the resource
 * slot the game reads when rendering that swatch's thumbnail and in-world
 * texture. The swatch_index itself is decided upstream by the Python mod's
 * PhotoAssignmentStore, not by this tool.
 *
 * @param {import("@s4tk/models").Package} pkg
 * @param {number} swatchIndex Zero-based swatch index.
 * @returns {import("@s4tk/models").ResourceEntry}
 */
function findTextureEntryForSwatch(pkg, swatchIndex) {
  if (!Number.isInteger(swatchIndex) || swatchIndex < 0) {
    throw new Error(`swatchIndex must be a non-negative integer, got: ${swatchIndex}`);
  }

  const entries = listTextureEntriesSorted(pkg);

  if (entries.length === 0) {
    throw new Error(
      "Template package has no DstImage (shuffled DDS) resources to use as " +
        "photo texture slots. If you passed packages/casp_template/base.package, " +
        "note that file is a known TODO of this project (built separately via " +
        "Sims4Studio/Wine) and may not exist yet - use " +
        "src/syntheticTemplate.js to generate a placeholder template for " +
        "development and tests."
    );
  }

  const entry = entries[swatchIndex];

  if (!entry) {
    throw new Error(
      `Template only has ${entries.length} swatch texture(s) (DstImage ` +
        `resources), but swatchIndex ${swatchIndex} was requested. Either the ` +
        "caller (PhotoAssignmentStore) is out of sync with this template, or " +
        "the template needs more swatches created in Sims4Studio."
    );
  }

  return entry;
}

/**
 * Replaces one swatch's texture resource in a template package with one
 * generated from the given photo, in place. The resource's original TGI key
 * (type/group/instance) is preserved on purpose: the CASP resource's
 * internal references point at that exact key (Sims4Studio wires this up
 * when the swatch is created), and we have no CASP-binary parser to rewrite
 * those references ourselves, so keeping the key stable is what makes the
 * accessory still resolve to the new texture in-game. Different Sims using
 * different swatch_index values overwrite different resource keys, so their
 * output packages coexist without clobbering each other.
 *
 * @param {import("@s4tk/models").Package} pkg Template package (mutated).
 * @param {Buffer} pngBuffer Raw PNG bytes of the user's photo.
 * @param {number} swatchIndex Zero-based swatch index (decided by the Python mod).
 * @returns {Promise<{ pkg: import("@s4tk/models").Package, textureKey: import("@s4tk/models").ResourceKey }>}
 */
async function assignPhotoToPackage(pkg, pngBuffer, swatchIndex) {
  const entry = findTextureEntryForSwatch(pkg, swatchIndex);
  entry.value = await pngBufferToTextureResource(pngBuffer);
  return { pkg, textureKey: entry.key };
}

/**
 * Writes a Package to disk, creating the destination directory if needed.
 *
 * @param {import("@s4tk/models").Package} pkg
 * @param {string} outputPath
 */
function writePackage(pkg, outputPath) {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, pkg.getBuffer());
}

/**
 * End-to-end helper: load template from disk, inject the photo, write the
 * resulting package to disk. This is what the CLI's `assign` command runs.
 *
 * @param {object} args
 * @param {string} args.templatePath
 * @param {Buffer} args.pngBuffer
 * @param {string} args.outputPath
 * @param {number} args.swatchIndex Zero-based swatch index (decided by the Python mod).
 * @returns {Promise<{ outputPath: string, textureKey: import("@s4tk/models").ResourceKey }>}
 */
async function assignPhotoToTemplateFile({ templatePath, pngBuffer, outputPath, swatchIndex }) {
  const pkg = loadTemplatePackage(templatePath);
  const { textureKey } = await assignPhotoToPackage(pkg, pngBuffer, swatchIndex);
  writePackage(pkg, outputPath);
  return { outputPath, textureKey };
}

module.exports = {
  loadTemplatePackage,
  listTextureEntriesSorted,
  findTextureEntryForSwatch,
  assignPhotoToPackage,
  writePackage,
  assignPhotoToTemplateFile,
};
