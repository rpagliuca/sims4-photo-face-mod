"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { PNG } = require("pngjs");

const { ATLAS, PHOTO_RECT, buildFaceAtlasPng, centerCropRect, makeSolidColorPng } = require("../../companion/src/png");

test("makeSolidColorPng produces a valid, decodable PNG", () => {
  const decoded = PNG.sync.read(makeSolidColorPng(6, [10, 20, 30, 255]));
  assert.equal(decoded.width, 6);
  assert.deepEqual([...decoded.data.subarray(0, 4)], [10, 20, 30, 255]);
});

test("centerCropRect keeps the full height of a wide image", () => {
  assert.deepEqual(centerCropRect({ width: 400, height: 100 }, 0.5), { x: 175, y: 0, width: 50, height: 100 });
});

test("centerCropRect keeps the full width of a tall image", () => {
  assert.deepEqual(centerCropRect({ width: 100, height: 400 }, 0.5), { x: 0, y: 100, width: 100, height: 200 });
});

test("buildFaceAtlasPng puts the opaque photo only in the glasses rectangle", () => {
  const atlas = PNG.sync.read(buildFaceAtlasPng(makeSolidColorPng(64, [200, 10, 20, 128])));
  assert.equal(atlas.width, ATLAS.width);
  assert.equal(atlas.height, ATLAS.height);
  const px = (x, y) => [...atlas.data.subarray((y * atlas.width + x) * 4, (y * atlas.width + x) * 4 + 4)];
  assert.deepEqual(px(PHOTO_RECT.x, PHOTO_RECT.y), [200, 10, 20, 255], "photo pixels are forced opaque");
  assert.deepEqual(px(PHOTO_RECT.x + PHOTO_RECT.width - 1, PHOTO_RECT.y + PHOTO_RECT.height - 1), [200, 10, 20, 255]);
  assert.equal(px(PHOTO_RECT.x - 1, PHOTO_RECT.y)[3], 0, "left of the rectangle is transparent");
  assert.equal(px(PHOTO_RECT.x, PHOTO_RECT.y + PHOTO_RECT.height)[3], 0, "below the rectangle is transparent");
  assert.equal(px(0, 0)[3], 0);
});
