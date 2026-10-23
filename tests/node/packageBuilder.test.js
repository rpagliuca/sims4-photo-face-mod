"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  CASP_RESOURCE_TYPE,
  addPhotoCasp,
  findTemplateCasp,
  loadTemplatePackage,
  readCaspTgis,
} = require("../../companion/src/packageBuilder");
const { makeSolidColorPng } = require("../../companion/src/png");
const { RLE2_RESOURCE_TYPE } = require("../../companion/src/rle2");
const { TEMPLATE_PATH } = require("./helpers");

const TEMPLATE_CASP = 0xc4a9939f6d089983n;
const casps = (pkg) => pkg.entries.filter((e) => e.key.type === CASP_RESOURCE_TYPE);

test("the real template has one CASP whose TGI list points at its RLE2 diffuse", () => {
  const pkg = loadTemplatePackage(TEMPLATE_PATH);
  const casp = findTemplateCasp(pkg);
  assert.equal(casp.key.instance, TEMPLATE_CASP);
  const diffuse = readCaspTgis(casp.value.getBuffer()).filter((t) => t.type === RLE2_RESOURCE_TYPE);
  assert.equal(diffuse.length, 1);
  assert.ok(pkg.entries.some((e) => e.key.type === RLE2_RESOURCE_TYPE && e.key.instance === diffuse[0].instance));
});

test("addPhotoCasp clones the CASP with a new texture, keeping meshes shared", async () => {
  const pkg = loadTemplatePackage(TEMPLATE_PATH);
  const before = pkg.entries.length;
  const { caspInstance, textureInstance } = await addPhotoCasp(pkg, "fulano", makeSolidColorPng(8));

  assert.equal(pkg.entries.length, before + 2);
  const clone = casps(pkg).find((e) => e.key.instance === caspInstance);
  const original = casps(pkg).find((e) => e.key.instance === TEMPLATE_CASP);
  const cloneTgis = readCaspTgis(clone.value.getBuffer());
  const originalTgis = readCaspTgis(original.value.getBuffer());
  assert.equal(cloneTgis.find((t) => t.type === RLE2_RESOURCE_TYPE).instance, textureInstance);
  assert.deepEqual(
    cloneTgis.filter((t) => t.type !== RLE2_RESOURCE_TYPE).map(({ at, ...t }) => t),
    originalTgis.filter((t) => t.type !== RLE2_RESOURCE_TYPE).map(({ at, ...t }) => t),
    "meshes and region map stay the template's"
  );
  assert.ok(pkg.entries.some((e) => e.key.type === RLE2_RESOURCE_TYPE && e.key.instance === textureInstance));
});

test("two photo_keys get distinct CASPs; re-running a key replaces it in place", async () => {
  const pkg = loadTemplatePackage(TEMPLATE_PATH);
  const a = await addPhotoCasp(pkg, "fulano", makeSolidColorPng(8));
  const generated = new Set([a.caspInstance]);
  const b = await addPhotoCasp(pkg, "ciclano", makeSolidColorPng(8), generated);
  generated.add(b.caspInstance);
  assert.notEqual(a.caspInstance, b.caspInstance);
  assert.notEqual(a.textureInstance, b.textureInstance);

  const count = pkg.entries.length;
  const again = await addPhotoCasp(pkg, "fulano", makeSolidColorPng(8, [1, 2, 3, 255]), generated);
  assert.equal(again.caspInstance, a.caspInstance);
  assert.equal(pkg.entries.length, count);
  assert.equal(casps(pkg).length, 3);
});

test("findTemplateCasp refuses an accumulated package when the manifest is lost", async () => {
  const pkg = loadTemplatePackage(TEMPLATE_PATH);
  await addPhotoCasp(pkg, "fulano", makeSolidColorPng(8));
  assert.throws(() => findTemplateCasp(pkg), /exatamente 1 CASP/);
});

test("each clone gets its own internal name and the TGI list still parses", async () => {
  const name = (buf) => {
    const len = buf[12];
    return Buffer.from(buf.subarray(13, 13 + len)).swap16().toString("utf16le");
  };
  const pkg = loadTemplatePackage(TEMPLATE_PATH);
  const a = await addPhotoCasp(pkg, "fulano", makeSolidColorPng(8));
  const byInstance = (i) => casps(pkg).find((e) => e.key.instance === i).value.getBuffer();
  const clone = byInstance(a.caspInstance);
  assert.equal(name(clone), "PhotoFace_fulano_Papelao");
  const tgis = readCaspTgis(clone);
  assert.equal(tgis.length, readCaspTgis(byInstance(TEMPLATE_CASP)).length);
  assert.equal(tgis.find((t) => t.type === RLE2_RESOURCE_TYPE).instance, a.textureInstance);
});
