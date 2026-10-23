"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { Package } = require("@s4tk/models");

const { main, runAssign } = require("../../companion/src/index");
const { CASP_RESOURCE_TYPE } = require("../../companion/src/packageBuilder");
const { makeSolidColorPng } = require("../../companion/src/png");
const { formatInstance, loadManifest } = require("../../companion/src/manifest");
const { TEMPLATE_PATH, makeTmpDir } = require("./helpers");

function setup(t) {
  const dir = makeTmpDir(t);
  const photo = (name, rgba) => {
    const p = path.join(dir, `${name}.png`);
    fs.writeFileSync(p, makeSolidColorPng(16, rgba));
    return p;
  };
  return {
    dir,
    photo,
    output: path.join(dir, "PhotoFaceMod.package"),
    manifest: path.join(dir, "photo_manifest.json"),
  };
}

test("runAssign() writes the package with the photo CASP and records it in the manifest", async (t) => {
  const s = setup(t);
  const result = await runAssign({
    photo: s.photo("fulano", [255, 0, 0, 255]),
    "photo-key": "fulano",
    manifest: s.manifest,
    "sim-name": "Fulano",
    template: TEMPLATE_PATH,
    output: s.output,
  });

  assert.deepEqual(loadManifest(s.manifest), { fulano: formatInstance(result.caspInstance) });
  const pkg = Package.from(fs.readFileSync(s.output));
  assert.ok(pkg.entries.some((e) => e.key.type === CASP_RESOURCE_TYPE && e.key.instance === result.caspInstance));
});

test("assign for two Sims accumulates both CASPs in one .package; re-running replaces", async (t) => {
  const s = setup(t);
  const run = (key, rgba) =>
    runAssign({ photo: s.photo(key, rgba), "photo-key": key, manifest: s.manifest, template: TEMPLATE_PATH, output: s.output });

  const fulano = await run("fulano", [255, 0, 0, 255]);
  const ciclano = await run("ciclano", [0, 0, 255, 255]);
  const fulanoAgain = await run("fulano", [0, 255, 0, 255]);

  assert.equal(fulanoAgain.caspInstance, fulano.caspInstance);
  assert.deepEqual(loadManifest(s.manifest), {
    ciclano: formatInstance(ciclano.caspInstance),
    fulano: formatInstance(fulano.caspInstance),
  });
  const pkg = Package.from(fs.readFileSync(s.output));
  const casps = pkg.entries.filter((e) => e.key.type === CASP_RESOURCE_TYPE).map((e) => e.key.instance);
  assert.equal(casps.length, 3, "template + 2 photos");
  assert.ok(casps.includes(fulano.caspInstance) && casps.includes(ciclano.caspInstance));
});

test("main() end-to-end via the `assign` subcommand", async (t) => {
  const s = setup(t);
  const originalWrite = process.stdout.write;
  let captured = "";
  process.stdout.write = (chunk) => {
    captured += chunk;
    return true;
  };
  try {
    await main([
      "assign",
      "--photo", s.photo("ciclana", [0, 255, 0, 255]),
      "--photo-key", "ciclana",
      "--manifest", s.manifest,
      "--template", TEMPLATE_PATH,
      "--output", s.output,
    ]);
  } finally {
    process.stdout.write = originalWrite;
  }
  assert.match(captured, /-> CASP 0x[0-9A-F]{16}/);
  assert.ok(fs.existsSync(s.output));
  assert.deepEqual(Object.keys(loadManifest(s.manifest)), ["ciclana"]);
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

test("runPack() builds one CASP per PNG, keyed by file name, from scratch", async (t) => {
  const { runPack } = require("../../companion/src/index");
  const s = setup(t);
  const dir = path.join(s.dir, "caras");
  fs.mkdirSync(dir);
  fs.writeFileSync(path.join(dir, "pirata.png"), makeSolidColorPng(16, [1, 2, 3, 255]));
  fs.writeFileSync(path.join(dir, "robo.png"), makeSolidColorPng(16, [4, 5, 6, 255]));
  fs.writeFileSync(path.join(dir, "leia-me.txt"), "ignorado");

  const result = await runPack({ dir, manifest: s.manifest, template: TEMPLATE_PATH, output: s.output });

  assert.deepEqual(result.keys, ["pirata", "robo"]);
  assert.deepEqual(Object.keys(loadManifest(s.manifest)).sort(), ["pirata", "robo"]);
  const pkg = Package.from(fs.readFileSync(s.output));
  assert.equal(pkg.entries.filter((e) => e.key.type === CASP_RESOURCE_TYPE).length, 3, "template + 2 caras");
});
