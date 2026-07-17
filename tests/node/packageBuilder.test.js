"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { Package, RawResource } = require("@s4tk/models");
const { BinaryResourceType } = require("@s4tk/models/enums");

const { createSyntheticTemplatePackage } = require("../../companion/src/syntheticTemplate");
const { findTextureEntry, assignPhotoToPackage } = require("../../companion/src/packageBuilder");
const { makeSolidColorPng } = require("../../companion/src/png");

test("synthetic template package is a parseable DBPF with a texture + CASP resource", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-1" });
  const buffer = pkg.getBuffer();

  assert.equal(buffer.subarray(0, 4).toString("ascii"), "DBPF");

  const reopened = Package.from(buffer);
  assert.equal(reopened.entries.length, 2);

  const textureEntry = reopened.entries.find((e) => e.key.type === BinaryResourceType.DstImage);
  const caspEntry = reopened.entries.find((e) => e.key.type === BinaryResourceType.CasPart);

  assert.ok(textureEntry, "expected a DstImage resource entry");
  assert.ok(caspEntry, "expected a CasPart resource entry");
  assert.equal(textureEntry.value.image.isShuffled, true);
});

test("assignPhotoToPackage replaces the texture but keeps its TGI key and the CASP resource intact", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-2" });
  const originalTextureEntry = findTextureEntry(pkg);
  const originalKey = { ...originalTextureEntry.key };
  const originalCaspBuffer = Buffer.from(
    pkg.entries.find((e) => e.key.type === BinaryResourceType.CasPart).value.buffer
  );

  const photo = makeSolidColorPng(8, [5, 6, 7, 255]);
  const { textureKey } = await assignPhotoToPackage(pkg, photo);

  assert.equal(textureKey.type, originalKey.type);
  assert.equal(textureKey.group, originalKey.group);
  assert.equal(textureKey.instance, originalKey.instance);

  const reopened = Package.from(pkg.getBuffer());
  const newTextureEntry = reopened.entries.find((e) => e.key.type === BinaryResourceType.DstImage);
  const caspEntry = reopened.entries.find((e) => e.key.type === BinaryResourceType.CasPart);

  assert.equal(newTextureEntry.key.instance, originalKey.instance);
  assert.equal(newTextureEntry.value.image.isShuffled, true);
  assert.ok(caspEntry.value.buffer.equals(originalCaspBuffer), "CASP placeholder must be untouched");
});

test("findTextureEntry throws a helpful error when the template has no DstImage resource", () => {
  const pkg = new Package([
    {
      key: { type: BinaryResourceType.CasPart, group: 0, instance: 1n },
      value: RawResource.from(Buffer.from("no texture here")),
    },
  ]);

  assert.throws(() => findTextureEntry(pkg), /DstImage/);
});
