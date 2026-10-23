"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

const { Package } = require("@s4tk/models");

const { RLE2_RESOURCE_TYPE, decodeRle2, encodeRle2FromDds } = require("../../companion/src/rle2");
const { TEMPLATE_PATH } = require("./helpers");

function ddsFromBlocks({ width, height, mipCount, blocks }) {
  const header = Buffer.alloc(128);
  header.write("DDS ", 0);
  header.writeUInt32LE(124, 4);
  header.writeUInt32LE(height, 12);
  header.writeUInt32LE(width, 16);
  header.writeUInt32LE(mipCount, 28);
  header.writeUInt32LE(0x35545844, 84);
  return Buffer.concat([header, blocks]);
}

test("decode + encode reproduces the RLE2 texture Sims4Studio wrote, byte for byte", () => {
  const pkg = Package.from(fs.readFileSync(TEMPLATE_PATH));
  const original = pkg.entries.find((e) => e.key.type === RLE2_RESOURCE_TYPE).value.getBuffer();
  const decoded = decodeRle2(original);
  assert.equal(decoded.width, 1024);
  assert.equal(decoded.height, 2048);
  assert.ok(encodeRle2FromDds(ddsFromBlocks(decoded)).equals(original));
});

test("encodeRle2FromDds rejects DDS files that are not DXT5", () => {
  const dds = ddsFromBlocks({ width: 4, height: 4, mipCount: 1, blocks: Buffer.alloc(16) });
  dds.writeUInt32LE(0x31545844, 84); // DXT1
  assert.throws(() => encodeRle2FromDds(dds), /DXT5/);
});
