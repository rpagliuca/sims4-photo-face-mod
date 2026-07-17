#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const { parseArgs } = require("node:util");

const { formatResourceKey } = require("@s4tk/hashing/formatting");

const {
  loadTemplatePackage,
  countSwatches,
  resolveBasePackagePath,
  assignPhotoToPackage,
  writePackage,
} = require("./packageBuilder");
const { loadManifest, saveManifest, allocateSwatchIndex } = require("./manifest");

const USAGE = `Usage:
  sims4-photo-face assign --photo <file.png> --photo-key <key> --manifest <photo_manifest.json> --template <template.package> --output <output.package> [--sim-name <name>] [--swatch-index <N>]

Options:
  --photo         Path to the user's PNG photo.
  --photo-key     Readable key the Python mod looks up at runtime (e.g. the
                   argument to "photofacemod.assign <photo_key>"). Re-running
                   with the same --photo-key reuses its existing swatch.
  --manifest      Path to photo_manifest.json (photo_key -> swatch_index),
                   read by the Python mod's PhotoManifest. Created if missing.
  --template      Path to the CAS Part template .package (with N pre-made
                   swatches) to clone on the very first run.
  --output        Path to write the resulting .package to. If this file
                   already exists, it is used as the base instead of
                   --template, so multiple Sims accumulate into one file.
  --sim-name      Optional label for logging only (not embedded in the
                   package; does not affect which resource is overwritten).
  --swatch-index  Optional advanced override: force a specific swatch index
                   instead of letting the manifest allocate/reuse one.
  --help          Show this message.
`;

/**
 * Parses argv (excluding node/script) into a command + options.
 *
 * @param {string[]} argv
 */
function parseCliArgs(argv) {
  const { values, positionals } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      photo: { type: "string" },
      "photo-key": { type: "string" },
      manifest: { type: "string" },
      "swatch-index": { type: "string" },
      "sim-name": { type: "string" },
      template: { type: "string" },
      output: { type: "string" },
      help: { type: "boolean", default: false },
    },
  });

  return { command: positionals[0], options: values };
}

/**
 * Runs the `assign` command:
 *  1. loads (or creates) the accumulated output package - or the template on
 *     the first run for this --output;
 *  2. loads (or creates) the photo_manifest.json;
 *  3. resolves photo_key -> swatch_index (reusing an existing mapping, or
 *     allocating the next free one; or honoring an explicit --swatch-index
 *     override);
 *  4. writes the photo into that swatch and saves both the .package and the
 *     manifest.
 *
 * `--sim-name` is accepted but only used for the log message - it does not
 * influence which resource gets overwritten (that's `--photo-key` via the
 * manifest), since per-Sim resource collisions are exactly what this design
 * must avoid.
 *
 * @param {{photo: string, "photo-key": string, manifest: string, template: string, output: string, "sim-name"?: string, "swatch-index"?: string}} options
 * @returns {Promise<{ outputPath: string, textureKey: import("@s4tk/models").ResourceKey, swatchIndex: number, manifestPath: string }>}
 */
async function runAssign(options) {
  const missing = ["photo", "photo-key", "manifest", "template", "output"].filter((key) => !options[key]);
  if (missing.length > 0) {
    throw new Error(`Missing required option(s): ${missing.map((k) => `--${k}`).join(", ")}\n\n${USAGE}`);
  }

  const photoKey = options["photo-key"];
  const basePath = resolveBasePackagePath({ templatePath: options.template, outputPath: options.output });
  const pkg = loadTemplatePackage(basePath);
  const swatchCount = countSwatches(pkg);

  const existingManifest = loadManifest(options.manifest);

  let manifest;
  let swatchIndex;

  if (options["swatch-index"] !== undefined) {
    swatchIndex = Number(options["swatch-index"]);
    if (!Number.isInteger(swatchIndex) || swatchIndex < 0) {
      throw new Error(`--swatch-index must be a non-negative integer, got: "${options["swatch-index"]}"\n\n${USAGE}`);
    }
    manifest = { ...existingManifest, [photoKey]: swatchIndex };
  } else {
    ({ manifest, swatchIndex } = allocateSwatchIndex(existingManifest, photoKey, swatchCount));
  }

  const pngBuffer = fs.readFileSync(options.photo);
  const { textureKey } = await assignPhotoToPackage(pkg, pngBuffer, swatchIndex);
  writePackage(pkg, options.output);
  saveManifest(options.manifest, manifest);

  return { outputPath: options.output, textureKey, swatchIndex, manifestPath: options.manifest };
}

/**
 * CLI entry point. Exported for testing; also invoked directly when this
 * file is run with `node`.
 *
 * @param {string[]} argv Arguments, excluding `node` and the script path.
 */
async function main(argv) {
  const { command, options } = parseCliArgs(argv);

  if (options.help || !command) {
    process.stdout.write(USAGE);
    return;
  }

  if (command !== "assign") {
    throw new Error(`Unknown command "${command}".\n\n${USAGE}`);
  }

  const { outputPath, textureKey, swatchIndex, manifestPath } = await runAssign(options);
  const label = options["sim-name"]
    ? `Sim "${options["sim-name"]}" (photo_key "${options["photo-key"]}")`
    : `photo_key "${options["photo-key"]}"`;
  process.stdout.write(
    `Assigned photo for ${label} -> swatch ${swatchIndex}\n` +
      `Package: ${outputPath}\n` +
      `Manifest: ${manifestPath}\n` +
      `Texture resource key: ${formatResourceKey(textureKey)}\n`
  );
}

if (require.main === module) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { main, parseCliArgs, runAssign };
