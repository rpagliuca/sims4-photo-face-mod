#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const { parseArgs } = require("node:util");

const {
  loadTemplatePackage,
  resolveBasePackagePath,
  addPhotoCasp,
  writePackage,
} = require("./packageBuilder");
const { loadManifest, saveManifest, generatedInstances, formatInstance } = require("./manifest");

const USAGE = `Usage:
  sims4-photo-face assign --photo <file.png> --photo-key <key> --manifest <photo_manifest.json> --template <base.package> --output <output.package> [--sim-name <name>]

Options:
  --photo         Path to the user's PNG photo.
  --photo-key     Readable key the Python mod looks up at runtime (the
                   argument to "photofacemod.assign <photo_key>"). Re-running
                   with the same --photo-key replaces that photo.
  --manifest      Path to photo_manifest.json (photo_key -> CASP instance),
                   read by the Python mod's PhotoManifest. Created if missing.
  --template      Path to packages/casp_template/base.package, cloned on the
                   very first run.
  --output        Path to write the resulting .package to. If this file
                   already exists, it is used as the base instead of
                   --template, so multiple photos accumulate into one file.
  --sim-name      Optional label for logging only.
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
      "sim-name": { type: "string" },
      template: { type: "string" },
      output: { type: "string" },
      help: { type: "boolean", default: false },
    },
  });

  return { command: positionals[0], options: values };
}

/**
 * Runs the `assign` command: clones the template CASP for this photo (a new
 * CASP + RLE2 texture, both with instances derived from the photo_key), adds
 * them to the accumulated output package and records photo_key -> CASP
 * instance in the manifest.
 *
 * @param {{photo: string, "photo-key": string, manifest: string, template: string, output: string, "sim-name"?: string}} options
 * @returns {Promise<{ outputPath: string, caspInstance: bigint, textureInstance: bigint, manifestPath: string }>}
 */
async function runAssign(options) {
  const missing = ["photo", "photo-key", "manifest", "template", "output"].filter((key) => !options[key]);
  if (missing.length > 0) {
    throw new Error(`Missing required option(s): ${missing.map((k) => `--${k}`).join(", ")}\n\n${USAGE}`);
  }

  const photoKey = options["photo-key"];
  const pkg = loadTemplatePackage(resolveBasePackagePath({ templatePath: options.template, outputPath: options.output }));
  const manifest = loadManifest(options.manifest);

  const { caspInstance, textureInstance } = await addPhotoCasp(
    pkg,
    photoKey,
    fs.readFileSync(options.photo),
    generatedInstances(manifest)
  );
  writePackage(pkg, options.output);
  saveManifest(options.manifest, { ...manifest, [photoKey]: formatInstance(caspInstance) });

  return { outputPath: options.output, caspInstance, textureInstance, manifestPath: options.manifest };
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

  const { outputPath, caspInstance, manifestPath } = await runAssign(options);
  const label = options["sim-name"]
    ? `Sim "${options["sim-name"]}" (photo_key "${options["photo-key"]}")`
    : `photo_key "${options["photo-key"]}"`;
  process.stdout.write(
    `Assigned photo for ${label} -> CASP ${formatInstance(caspInstance)}\n` +
      `Package: ${outputPath}\n` +
      `Manifest: ${manifestPath}\n`
  );
}

if (require.main === module) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { main, parseCliArgs, runAssign };
