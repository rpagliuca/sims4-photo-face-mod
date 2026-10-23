"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const { loadManifest, saveManifest, generatedInstances, formatInstance } = require("../../companion/src/manifest");
const { makeTmpDir } = require("./helpers");

test("loadManifest returns {} when the file doesn't exist yet", (t) => {
  assert.deepEqual(loadManifest(path.join(makeTmpDir(t), "does-not-exist.json")), {});
});

test("saveManifest + loadManifest round-trip, creating parent directories", (t) => {
  const manifestPath = path.join(makeTmpDir(t), "nested", "photo_manifest.json");
  const manifest = { rafael: "0x8000000000000001", irmao: "0x8000000000000002" };
  saveManifest(manifestPath, manifest);
  assert.deepEqual(loadManifest(manifestPath), manifest);
});

test("formatInstance writes 16 uppercase hex digits with 0x", () => {
  assert.equal(formatInstance(0xabcn), "0x0000000000000ABC");
});

test("generatedInstances parses the manifest values back to bigint", () => {
  const set = generatedInstances({ a: "0x8000000000000001", b: "0x00000000000000FF" });
  assert.deepEqual([...set], [0x8000000000000001n, 0xffn]);
});
