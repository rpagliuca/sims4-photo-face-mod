"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const { loadManifest, saveManifest, allocateSwatchIndex } = require("../../companion/src/manifest");

function makeTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "photoface-manifest-test-"));
}

test("loadManifest returns {} when the file doesn't exist yet", () => {
  const dir = makeTmpDir();
  const manifest = loadManifest(path.join(dir, "does-not-exist.json"));
  assert.deepEqual(manifest, {});
  fs.rmSync(dir, { recursive: true, force: true });
});

test("saveManifest + loadManifest round-trip, creating parent directories", () => {
  const dir = makeTmpDir();
  const manifestPath = path.join(dir, "nested", "photo_manifest.json");

  saveManifest(manifestPath, { rafael: 0, irmao: 1 });
  assert.deepEqual(loadManifest(manifestPath), { rafael: 0, irmao: 1 });

  fs.rmSync(dir, { recursive: true, force: true });
});

test("allocateSwatchIndex assigns the first free index for a new photo_key", () => {
  const { manifest, swatchIndex } = allocateSwatchIndex({ rafael: 0 }, "irmao", 4);
  assert.equal(swatchIndex, 1);
  assert.deepEqual(manifest, { rafael: 0, irmao: 1 });
});

test("allocateSwatchIndex reuses the existing index for an already-known photo_key", () => {
  const existing = { rafael: 0, irmao: 1 };
  const { manifest, swatchIndex } = allocateSwatchIndex(existing, "rafael", 4);
  assert.equal(swatchIndex, 0);
  assert.equal(manifest, existing, "should return the same manifest reference, unmodified");
});

test("allocateSwatchIndex fills gaps left by previously-freed indices", () => {
  const { swatchIndex } = allocateSwatchIndex({ a: 0, c: 2 }, "b", 4);
  assert.equal(swatchIndex, 1);
});

test("allocateSwatchIndex throws a clear error when all swatches are taken", () => {
  const full = { a: 0, b: 1 };
  assert.throws(() => allocateSwatchIndex(full, "c", 2), /No free swatch index/);
});
