"use strict";

const fs = require("node:fs");
const path = require("node:path");

const { Package, RawResource } = require("@s4tk/models");
const { BinaryResourceType } = require("@s4tk/models/enums");

const { pngBufferToTextureResource } = require("./texture");
const { makeSolidColorPng } = require("./png");
const { DEFAULT_GROUP, deriveInstanceId } = require("./resourceKeys");

/** Default number of placeholder swatches, matching the low end of the
 * "8-16 to start" recommendation in packages/casp_template/README.md - kept
 * small here since tests don't need many, just more than one. */
const DEFAULT_SWATCH_COUNT = 4;

/**
 * KNOWN PROJECT TODO: there is no real CAS Part template yet. The real one
 * (packages/casp_template/base.package) is built out-of-band with
 * Sims4Studio, which creates one DstImage texture resource per swatch and
 * wires the CASP resource's internal references to each swatch's own key
 * (Sims4Studio's job, not ours - we have no CASP binary parser). This module
 * exists purely so the companion's logic and its tests have something
 * concrete to load with multiple independent swatches, without depending on
 * that external artifact existing.
 *
 * The fixture below is NOT a valid in-game CAS Part - the CasPart resource is
 * a placeholder blob, not real CASP binary tuning data, and it does NOT
 * reference the swatch textures the way a real CASP would (we have no way to
 * fabricate that without a CASP writer). It is only realistic enough to
 * exercise DBPF read/write and "find + replace one swatch's texture
 * resource, by index" end to end.
 *
 * @param {object} [options]
 * @param {string} [options.label] Distinguishes instance IDs between fixtures.
 * @param {number} [options.swatchCount] How many DstImage swatch resources to generate.
 * @returns {Promise<import("@s4tk/models").Package>}
 */
async function createSyntheticTemplatePackage(options = {}) {
  const { label = "synthetic-template", swatchCount = DEFAULT_SWATCH_COUNT } = options;

  const swatchEntries = await Promise.all(
    Array.from({ length: swatchCount }, async (_, swatchIndex) => {
      const key = {
        type: BinaryResourceType.DstImage,
        group: DEFAULT_GROUP,
        instance: deriveInstanceId(label, `texture-swatch-${swatchIndex}`),
      };
      // Distinct placeholder color per swatch, purely so a human inspecting
      // the fixture package can tell swatches apart; irrelevant to the game.
      const shade = 40 + swatchIndex * 40;
      const placeholderPhoto = makeSolidColorPng(8, [shade, shade, shade, 255]);
      const value = await pngBufferToTextureResource(placeholderPhoto);
      return { key, value };
    })
  );

  const caspKey = {
    type: BinaryResourceType.CasPart,
    group: DEFAULT_GROUP,
    instance: deriveInstanceId(label, "casp"),
  };

  const caspResource = RawResource.from(
    Buffer.from(`FAKE-CASP-PLACEHOLDER:${label}:${swatchCount}-swatches`, "utf8")
  );

  return new Package([...swatchEntries, { key: caspKey, value: caspResource }]);
}

/**
 * Convenience wrapper that writes the synthetic template straight to a file,
 * matching the on-disk .package interface the CLI's --template flag expects.
 *
 * @param {string} outputPath
 * @param {object} [options] Forwarded to createSyntheticTemplatePackage.
 * @returns {Promise<string>} The path written to.
 */
async function writeSyntheticTemplatePackage(outputPath, options = {}) {
  const pkg = await createSyntheticTemplatePackage(options);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, pkg.getBuffer());
  return outputPath;
}

module.exports = {
  DEFAULT_SWATCH_COUNT,
  createSyntheticTemplatePackage,
  writeSyntheticTemplatePackage,
};
