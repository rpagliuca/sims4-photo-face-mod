"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { PNG } = require("pngjs");

const { cropToSquarePng, makeSolidColorPng } = require("../../companion/src/png");

function makeGradientPng(width, height) {
  const png = new PNG({ width, height });
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const offset = (y * width + x) * 4;
      png.data[offset] = x * 10;
      png.data[offset + 1] = y * 10;
      png.data[offset + 2] = 0;
      png.data[offset + 3] = 255;
    }
  }
  return PNG.sync.write(png);
}

test("cropToSquarePng centers the crop on the longer axis", () => {
  const source = makeGradientPng(4, 2);
  const cropped = PNG.sync.read(cropToSquarePng(source));

  assert.equal(cropped.width, 2);
  assert.equal(cropped.height, 2);

  const pixel = (img, x, y) => {
    const offset = (y * img.width + x) * 4;
    return [img.data[offset], img.data[offset + 1]];
  };

  // offsetX = floor((4 - 2) / 2) = 1, offsetY = 0
  assert.deepEqual(pixel(cropped, 0, 0), [10, 0]);
  assert.deepEqual(pixel(cropped, 1, 0), [20, 0]);
  assert.deepEqual(pixel(cropped, 0, 1), [10, 10]);
  assert.deepEqual(pixel(cropped, 1, 1), [20, 10]);
});

test("cropToSquarePng is a no-op for already-square images", () => {
  const source = makeGradientPng(3, 3);
  const cropped = cropToSquarePng(source);
  assert.ok(source.equals(cropped));
});

test("makeSolidColorPng produces a valid, decodable PNG", () => {
  const buffer = makeSolidColorPng(6, [10, 20, 30, 255]);

  assert.deepEqual([...buffer.subarray(0, 8)], [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

  const decoded = PNG.sync.read(buffer);
  assert.equal(decoded.width, 6);
  assert.equal(decoded.height, 6);
  assert.deepEqual([decoded.data[0], decoded.data[1], decoded.data[2], decoded.data[3]], [10, 20, 30, 255]);
});
