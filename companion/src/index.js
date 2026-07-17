#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const { parseArgs } = require("node:util");

const { formatResourceKey } = require("@s4tk/hashing/formatting");

const { assignPhotoToTemplateFile } = require("./packageBuilder");

const USAGE = `Usage:
  sims4-photo-face assign --photo <file.png> --swatch-index <N> --template <template.package> --output <output.package> [--sim-name <name>]

Options:
  --photo         Path to the user's PNG photo.
  --swatch-index  Zero-based CAS swatch index to overwrite (decided by the
                   Python mod's PhotoAssignmentStore, not by this CLI).
  --template      Path to the CAS Part template .package to clone.
  --output        Path to write the resulting .package to.
  --sim-name      Optional label for logging only (not embedded in the
                   package; does not affect which resource is overwritten).
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
 * Runs the `assign` command: reads the photo + template from disk, injects
 * the photo into the given swatch's CAS Part texture, and writes the
 * resulting package. `--sim-name` is accepted but only used for the log
 * message - it does not influence which resource gets overwritten, since
 * that's exactly the per-Sim collision this CLI must NOT reintroduce (see
 * swatch-index below).
 *
 * @param {{photo: string, "swatch-index": string, template: string, output: string, "sim-name"?: string}} options
 * @returns {Promise<{ outputPath: string, textureKey: import("@s4tk/models").ResourceKey }>}
 */
async function runAssign(options) {
  const missing = ["photo", "swatch-index", "template", "output"].filter((key) => !options[key]);
  if (missing.length > 0) {
    throw new Error(`Missing required option(s): ${missing.map((k) => `--${k}`).join(", ")}\n\n${USAGE}`);
  }

  const swatchIndex = Number(options["swatch-index"]);
  if (!Number.isInteger(swatchIndex) || swatchIndex < 0) {
    throw new Error(`--swatch-index must be a non-negative integer, got: "${options["swatch-index"]}"\n\n${USAGE}`);
  }

  const pngBuffer = fs.readFileSync(options.photo);

  return assignPhotoToTemplateFile({
    templatePath: options.template,
    pngBuffer,
    outputPath: options.output,
    swatchIndex,
  });
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

  const { outputPath, textureKey } = await runAssign(options);
  const label = options["sim-name"] ? `Sim "${options["sim-name"]}" (swatch ${options["swatch-index"]})` : `swatch ${options["swatch-index"]}`;
  process.stdout.write(
    `Assigned photo for ${label} -> ${outputPath}\n` + `Texture resource key: ${formatResourceKey(textureKey)}\n`
  );
}

if (require.main === module) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { main, parseCliArgs, runAssign };
