"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { DdsImage } = require("@s4tk/images");

const { makeSolidColorPng } = require("../../companion/src/png");
const { pngBufferToDdsImage, pngBufferToTextureResource } = require("../../companion/src/texture");

test("pngBufferToDdsImage produces a valid, shuffled (DST) DDS image", async () => {
  const png = makeSolidColorPng(8, [200, 50, 50, 255]);
  const dds = await pngBufferToDdsImage(png);

  assert.equal(dds.buffer.readUInt32LE(0), DdsImage.SIGNATURE, "should start with the DDS magic bytes");
  assert.equal(dds.isShuffled, true, "conversion must request shuffle:true (DST) for CAS Part textures");
});

test("pngBufferToDdsImage crops non-square photos before converting", async () => {
  const { PNG } = require("pngjs");
  const wide = new PNG({ width: 16, height: 8 });
  wide.data.fill(128);
  const png = PNG.sync.write(wide);

  const dds = await pngBufferToDdsImage(png);
  assert.equal(dds.buffer.readUInt32LE(0), DdsImage.SIGNATURE);
});

test("pngBufferToTextureResource wraps the DDS image in a DdsImageResource", async () => {
  const png = makeSolidColorPng(8, [10, 200, 10, 255]);
  const resource = await pngBufferToTextureResource(png);

  assert.equal(resource.image.isShuffled, true);
  assert.ok(resource.buffer.length > 0);
});
