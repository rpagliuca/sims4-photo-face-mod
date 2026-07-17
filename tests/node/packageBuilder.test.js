"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { Package, RawResource } = require("@s4tk/models");
const { BinaryResourceType } = require("@s4tk/models/enums");

const { createSyntheticTemplatePackage } = require("../../companion/src/syntheticTemplate");
const {
  listTextureEntriesSorted,
  findTextureEntryForSwatch,
  assignPhotoToPackage,
} = require("../../companion/src/packageBuilder");
const { makeSolidColorPng } = require("../../companion/src/png");

test("synthetic template package is a parseable DBPF with N swatch textures + a CASP resource", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-1", swatchCount: 4 });
  const buffer = pkg.getBuffer();

  assert.equal(buffer.subarray(0, 4).toString("ascii"), "DBPF");

  const reopened = Package.from(buffer);
  assert.equal(reopened.entries.length, 5); // 4 swatches + 1 CASP

  const textureEntries = reopened.entries.filter((e) => e.key.type === BinaryResourceType.DstImage);
  const caspEntry = reopened.entries.find((e) => e.key.type === BinaryResourceType.CasPart);

  assert.equal(textureEntries.length, 4);
  assert.ok(caspEntry, "expected a CasPart resource entry");
  for (const entry of textureEntries) {
    assert.equal(entry.value.image.isShuffled, true);
  }
});

test("findTextureEntryForSwatch picks a distinct, deterministic resource per index", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-swatches", swatchCount: 4 });

  const sorted = listTextureEntriesSorted(pkg);
  assert.equal(sorted.length, 4);

  for (let i = 0; i < sorted.length; i++) {
    const entry = findTextureEntryForSwatch(pkg, i);
    assert.equal(entry.key.instance, sorted[i].key.instance);
  }

  // Same call, same result - selection must be deterministic, not random/order-of-Map-insertion dependent.
  assert.equal(findTextureEntryForSwatch(pkg, 2).key.instance, findTextureEntryForSwatch(pkg, 2).key.instance);
});

test("findTextureEntryForSwatch throws for an out-of-range index", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-range", swatchCount: 2 });
  assert.throws(() => findTextureEntryForSwatch(pkg, 2), /only has 2 swatch/);
});

test("findTextureEntryForSwatch throws for a non-integer/negative index", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-invalid", swatchCount: 2 });
  assert.throws(() => findTextureEntryForSwatch(pkg, -1), /non-negative integer/);
  assert.throws(() => findTextureEntryForSwatch(pkg, 1.5), /non-negative integer/);
});

test("findTextureEntryForSwatch throws a helpful error when the template has no DstImage resource at all", () => {
  const pkg = new Package([
    {
      key: { type: BinaryResourceType.CasPart, group: 0, instance: 1n },
      value: RawResource.from(Buffer.from("no texture here")),
    },
  ]);

  assert.throws(() => findTextureEntryForSwatch(pkg, 0), /DstImage/);
});

test("assignPhotoToPackage replaces only the requested swatch's texture, keeping its TGI key and the CASP resource intact", async () => {
  const pkg = await createSyntheticTemplatePackage({ label: "test-fixture-2", swatchCount: 3 });
  const originalEntries = listTextureEntriesSorted(pkg).map((e) => ({ ...e.key }));
  const originalCaspBuffer = Buffer.from(
    pkg.entries.find((e) => e.key.type === BinaryResourceType.CasPart).value.buffer
  );

  const photo = makeSolidColorPng(8, [5, 6, 7, 255]);
  const { textureKey } = await assignPhotoToPackage(pkg, photo, 1);

  assert.equal(textureKey.instance, originalEntries[1].instance);

  const reopened = Package.from(pkg.getBuffer());
  const sortedAfter = listTextureEntriesSorted(reopened);
  const caspEntry = reopened.entries.find((e) => e.key.type === BinaryResourceType.CasPart);

  // Swatch 1 was overwritten (still same key, new pixel content)...
  assert.equal(sortedAfter[1].key.instance, originalEntries[1].instance);
  assert.equal(sortedAfter[1].value.image.isShuffled, true);
  // ...but swatches 0 and 2 kept their original keys, untouched.
  assert.equal(sortedAfter[0].key.instance, originalEntries[0].instance);
  assert.equal(sortedAfter[2].key.instance, originalEntries[2].instance);
  assert.ok(caspEntry.value.buffer.equals(originalCaspBuffer), "CASP placeholder must be untouched");
});

test("two Sims assigned to different swatch indices overwrite different resource keys (no collision)", async () => {
  // Same label => the same deterministic template (as if both companion runs
  // were pointed at the same base.package): identical keys AND identical
  // starting placeholder bytes per swatch, since instance derivation and
  // placeholder generation are both pure functions of (label, index).
  const reference = await createSyntheticTemplatePackage({ label: "shared-template", swatchCount: 4 });
  const untouchedSwatch1Bytes = Buffer.from(listTextureEntriesSorted(reference)[1].value.buffer);

  const pkgA = await createSyntheticTemplatePackage({ label: "shared-template", swatchCount: 4 });
  const pkgB = await createSyntheticTemplatePackage({ label: "shared-template", swatchCount: 4 });

  const photoA = makeSolidColorPng(8, [255, 0, 0, 255]);
  const photoB = makeSolidColorPng(8, [0, 0, 255, 255]);

  const { textureKey: keyA } = await assignPhotoToPackage(pkgA, photoA, 0);
  const { textureKey: keyB } = await assignPhotoToPackage(pkgB, photoB, 1);

  assert.notEqual(keyA.instance, keyB.instance, "different swatch indices must map to different resource keys");

  // pkgA only touched swatch 0 - swatch 1 in pkgA must be byte-identical to
  // the pristine reference template's swatch 1 (proves no cross-swatch
  // contamination within the same package).
  const swatch1InA = listTextureEntriesSorted(pkgA)[1];
  assert.ok(Buffer.from(swatch1InA.value.buffer).equals(untouchedSwatch1Bytes));

  // And pkgB's swatch 0 (which it did NOT touch, since it assigned index 1)
  // is likewise still the pristine placeholder - so installing both pkgA and
  // pkgB together, each overwriting a different resource key, does not make
  // one Sim's photo clobber the other's.
  const swatch0InB = listTextureEntriesSorted(pkgB)[0];
  const untouchedSwatch0Bytes = Buffer.from(listTextureEntriesSorted(reference)[0].value.buffer);
  assert.ok(Buffer.from(swatch0InB.value.buffer).equals(untouchedSwatch0Bytes));
});
