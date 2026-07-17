"use strict";

const fs = require("node:fs");
const path = require("node:path");

/**
 * Loads photo_manifest.json (photo_key -> swatch_index), the file the
 * Python mod's PhotoManifest (src/photo_face_mod/manifest.py) reads at
 * runtime to resolve `photofacemod.assign <photo_key>`. Returns an empty
 * object if the file doesn't exist yet (first run).
 *
 * @param {string} manifestPath
 * @returns {Record<string, number>}
 */
function loadManifest(manifestPath) {
  if (!fs.existsSync(manifestPath)) {
    return {};
  }
  const raw = fs.readFileSync(manifestPath, "utf8");
  return raw.trim() ? JSON.parse(raw) : {};
}

/**
 * Writes photo_manifest.json, creating the destination directory if needed.
 * Keys are sorted for stable diffs across runs.
 *
 * @param {string} manifestPath
 * @param {Record<string, number>} manifest
 */
function saveManifest(manifestPath, manifest) {
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  const sortedKeys = Object.keys(manifest).sort();
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, sortedKeys, 2)}\n`);
}

/**
 * Resolves the swatch_index for a photo_key, allocating a new one if the key
 * isn't already in the manifest. Re-running for the same photo_key reuses
 * its existing index (so updating a Sim's photo doesn't grow the manifest).
 * Pure function - returns a new manifest object rather than mutating the one
 * passed in.
 *
 * @param {Record<string, number>} manifest
 * @param {string} photoKey
 * @param {number} swatchCount Total number of swatches available in the template.
 * @returns {{ manifest: Record<string, number>, swatchIndex: number }}
 */
function allocateSwatchIndex(manifest, photoKey, swatchCount) {
  if (Object.prototype.hasOwnProperty.call(manifest, photoKey)) {
    return { manifest, swatchIndex: manifest[photoKey] };
  }

  const usedIndices = new Set(Object.values(manifest));

  for (let index = 0; index < swatchCount; index++) {
    if (!usedIndices.has(index)) {
      return { manifest: { ...manifest, [photoKey]: index }, swatchIndex: index };
    }
  }

  throw new Error(
    `No free swatch index for photo_key "${photoKey}": all ${swatchCount} swatches in ` +
      "the CASP template are already assigned in the manifest. Add more swatches to the " +
      "template (packages/casp_template) to support more Sims."
  );
}

module.exports = { loadManifest, saveManifest, allocateSwatchIndex };
