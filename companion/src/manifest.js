"use strict";

const fs = require("node:fs");
const path = require("node:path");

/**
 * Loads photo_manifest.json (photo_key -> CASP instance, as a "0x..." hex
 * string), the file the
 * Python mod's PhotoManifest (src/photo_face_mod/manifest.py) reads at
 * runtime to resolve `photofacemod.assign <photo_key>`. Returns an empty
 * object if the file doesn't exist yet (first run).
 *
 * @param {string} manifestPath
 * @returns {Record<string, string>}
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
 * @param {Record<string, string>} manifest
 */
function saveManifest(manifestPath, manifest) {
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  const sortedKeys = Object.keys(manifest).sort();
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, sortedKeys, 2)}\n`);
}

/**
 * Instance ids of the CASPs this tool already generated, from the manifest
 * values ("0x..." hex strings).
 *
 * @param {Record<string, string>} manifest
 * @returns {Set<bigint>}
 */
function generatedInstances(manifest) {
  return new Set(Object.values(manifest).map((v) => BigInt(v)));
}

/**
 * Formats a CASP instance the way the manifest stores it (and the Python
 * mod parses it with int(value, 16)).
 *
 * @param {bigint} instance
 * @returns {string}
 */
function formatInstance(instance) {
  return `0x${instance.toString(16).toUpperCase().padStart(16, "0")}`;
}

module.exports = { loadManifest, saveManifest, generatedInstances, formatInstance };
