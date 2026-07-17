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
const { loadManifest } = require("../../companion/src/manifest");

function makeTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "photoface-cli-test-"));
}

test("runAssign() produces a valid output .package and writes the manifest", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test" });

  // 4px is the minimum @s4tk/images accepts for DDS conversion; still a tiny
  // fixture, no need for a versioned binary PNG file.
  const photoPath = path.join(dir, "photo.png");
  fs.writeFileSync(photoPath, makeSolidColorPng(4, [255, 0, 0, 255]));

  const outputPath = path.join(dir, "PhotoFaceMod.package");
  const manifestPath = path.join(dir, "photo_manifest.json");

  const result = await runAssign({
    photo: photoPath,
    "photo-key": "rafael",
    manifest: manifestPath,
    "sim-name": "Fulano",
    template: templatePath,
    output: outputPath,
  });

  assert.equal(result.outputPath, outputPath);
  assert.equal(result.swatchIndex, 0);
  assert.ok(fs.existsSync(outputPath));

  const manifest = loadManifest(manifestPath);
  assert.deepEqual(manifest, { rafael: 0 });

  const pkg = Package.from(fs.readFileSync(outputPath));
  const textureEntry = pkg.entries.find(
    (e) => e.key.type === BinaryResourceType.DstImage && e.key.instance === result.textureKey.instance
  );
  assert.ok(textureEntry, "expected the allocated swatch's resource key to be present in the output");
  assert.equal(textureEntry.value.image.isShuffled, true);
});

test("main() end-to-end via the `assign` subcommand", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test-e2e" });

  const photoPath = path.join(dir, "photo.png");
  fs.writeFileSync(photoPath, makeSolidColorPng(4, [0, 255, 0, 255]));

  const outputPath = path.join(dir, "PhotoFaceMod.package");
  const manifestPath = path.join(dir, "photo_manifest.json");

  await main([
    "assign",
    "--photo",
    photoPath,
    "--photo-key",
    "ciclana",
    "--manifest",
    manifestPath,
    "--sim-name",
    "Ciclana",
    "--template",
    templatePath,
    "--output",
    outputPath,
  ]);

  assert.ok(fs.existsSync(outputPath));
  assert.deepEqual(loadManifest(manifestPath), { ciclana: 0 });
});

test("running assign twice for the same --output accumulates both Sims' textures in one .package", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test-accumulate", swatchCount: 4 });

  const outputPath = path.join(dir, "PhotoFaceMod.package");
  const manifestPath = path.join(dir, "photo_manifest.json");

  const photoRafaelPath = path.join(dir, "rafael.png");
  fs.writeFileSync(photoRafaelPath, makeSolidColorPng(4, [255, 0, 0, 255]));
  const photoIrmaoPath = path.join(dir, "irmao.png");
  fs.writeFileSync(photoIrmaoPath, makeSolidColorPng(4, [0, 0, 255, 255]));

  const resultRafael = await runAssign({
    photo: photoRafaelPath,
    "photo-key": "rafael",
    manifest: manifestPath,
    template: templatePath,
    output: outputPath,
  });

  const resultIrmao = await runAssign({
    photo: photoIrmaoPath,
    "photo-key": "irmao",
    manifest: manifestPath,
    template: templatePath,
    output: outputPath,
  });

  assert.notEqual(resultRafael.swatchIndex, resultIrmao.swatchIndex);
  assert.notEqual(resultRafael.textureKey.instance, resultIrmao.textureKey.instance);

  assert.deepEqual(loadManifest(manifestPath), { rafael: resultRafael.swatchIndex, irmao: resultIrmao.swatchIndex });

  // The single accumulated output package must contain BOTH overwritten
  // resource keys - not just the last one written.
  const pkg = Package.from(fs.readFileSync(outputPath));
  const keys = pkg.entries.filter((e) => e.key.type === BinaryResourceType.DstImage).map((e) => e.key.instance);

  assert.ok(keys.includes(resultRafael.textureKey.instance), "rafael's swatch must still be present");
  assert.ok(keys.includes(resultIrmao.textureKey.instance), "irmao's swatch must still be present");
});

test("re-running assign for the same photo_key reuses its existing swatch instead of allocating a new one", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test-reuse" });

  const outputPath = path.join(dir, "PhotoFaceMod.package");
  const manifestPath = path.join(dir, "photo_manifest.json");

  const firstPhoto = path.join(dir, "first.png");
  fs.writeFileSync(firstPhoto, makeSolidColorPng(4, [10, 20, 30, 255]));
  const updatedPhoto = path.join(dir, "updated.png");
  fs.writeFileSync(updatedPhoto, makeSolidColorPng(4, [200, 210, 220, 255]));

  const first = await runAssign({
    photo: firstPhoto,
    "photo-key": "rafael",
    manifest: manifestPath,
    template: templatePath,
    output: outputPath,
  });

  const second = await runAssign({
    photo: updatedPhoto,
    "photo-key": "rafael",
    manifest: manifestPath,
    template: templatePath,
    output: outputPath,
  });

  assert.equal(second.swatchIndex, first.swatchIndex);
  assert.deepEqual(loadManifest(manifestPath), { rafael: first.swatchIndex });
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

test("main() rejects a non-integer --swatch-index override", async (t) => {
  const dir = makeTmpDir();
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const templatePath = path.join(dir, "template.package");
  await writeSyntheticTemplatePackage(templatePath, { label: "cli-test-bad-index" });

  const photoPath = path.join(dir, "photo.png");
  fs.writeFileSync(photoPath, makeSolidColorPng(4, [0, 0, 255, 255]));

  await assert.rejects(
    () =>
      main([
        "assign",
        "--photo",
        photoPath,
        "--photo-key",
        "rafael",
        "--manifest",
        path.join(dir, "photo_manifest.json"),
        "--swatch-index",
        "not-a-number",
        "--template",
        templatePath,
        "--output",
        path.join(dir, "out.package"),
      ]),
    /non-negative integer/
  );
});
