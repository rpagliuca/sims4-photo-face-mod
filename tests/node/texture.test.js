"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { PHOTO_RECT, makeSolidColorPng } = require("../../companion/src/png");
const { blockAlphas, decodeRle2 } = require("../../companion/src/rle2");
const { photoToRle2 } = require("../../companion/src/texture");

test("photoToRle2 makes a 1024x2048 RLE2 atlas, opaque only in the photo rectangle", async () => {
  const decoded = decodeRle2(await photoToRle2(makeSolidColorPng(32, [0, 128, 255, 255])));
  assert.equal(decoded.width, 1024);
  assert.equal(decoded.height, 2048);
  assert.ok(decoded.mipCount > 1, "keeps the mip chain");

  const blocksPerRow = 1024 / 4;
  const alphaOfBlock = (bx, by) => blockAlphas(decoded.blocks, (by * blocksPerRow + bx) * 16);
  const inside = alphaOfBlock(PHOTO_RECT.x / 4 + 1, PHOTO_RECT.y / 4 + 1);
  assert.ok(inside.every((a) => a === 255));
  assert.ok(alphaOfBlock(0, 0).every((a) => a === 0));
  assert.ok(alphaOfBlock(PHOTO_RECT.x / 4 - 1, PHOTO_RECT.y / 4).every((a) => a === 0));
});
