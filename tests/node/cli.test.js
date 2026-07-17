"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const { Package } = require("@s4tk/models");
const { BinaryResourceType } = require("@s4tk/models/enums");

const { main, runAssign } = require("../../companion/src/index");
const { writeSyntheticTemplatePackage } = require("../../companion/src/syntheticTemplate");
const { makeSolidColorPng } = require("../../companion/src/png");

function makeTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "photoface-cli-test-"));
}

test("runAssign() produces a valid output .package from a photo + template", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test" });

  // 4px is the minimum @s4tk/images accepts for DDS conversion; still a tiny
  // fixture, no need for a versioned binary PNG file.
  const photoPath = path.join(dir, "photo.png");
  fs.writeFileSync(photoPath, makeSolidColorPng(4, [255, 0, 0, 255]));

  const outputPath = path.join(dir, "Fulano_photo.package");

  const result = await runAssign({
    photo: photoPath,
    "sim-name": "Fulano",
    template: templatePath,
    output: outputPath,
  });

  assert.equal(result.outputPath, outputPath);
  assert.ok(fs.existsSync(outputPath));

  const pkg = Package.from(fs.readFileSync(outputPath));
  const textureEntry = pkg.entries.find((e) => e.key.type === BinaryResourceType.DstImage);
  assert.ok(textureEntry);
  assert.equal(textureEntry.value.image.isShuffled, true);
  assert.equal(textureEntry.key.instance, result.textureKey.instance);
});

test("main() end-to-end via the `assign` subcommand", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test-e2e" });

  const photoPath = path.join(dir, "photo.png");
  fs.writeFileSync(photoPath, makeSolidColorPng(4, [0, 255, 0, 255]));

  const outputPath = path.join(dir, "Ciclana_photo.package");

  await main([
    "assign",
    "--photo",
    photoPath,
    "--sim-name",
    "Ciclana",
    "--template",
    templatePath,
    "--output",
    outputPath,
  ]);

  assert.ok(fs.existsSync(outputPath));
});

test("main() prints usage when called with --help", async () => {
  const originalWrite = process.stdout.write;
  let captured = "";
  process.stdout.write = (chunk) => {
    captured += chunk;
    return true;
  };

  try {
    await main(["--help"]);
  } finally {
    process.stdout.write = originalWrite;
  }

  assert.match(captured, /Usage:/);
});

test("runAssign() rejects when required options are missing", async () => {
  await assert.rejects(() => runAssign({}), /Missing required option/);
});
