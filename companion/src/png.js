"use strict";

const { PNG } = require("pngjs");

/**
 * Crops a decoded PNG buffer to a centered square (min(width, height) side).
 * This is the MVP "no perspective, no fuss" crop the tosco billboard needs:
 * DdsImage.fromImageAsync() would otherwise stretch non-square photos
 * independently on each axis when rounding up to a power-of-2 texture size.
 *
 * @param {Buffer} pngBuffer Raw PNG file bytes.
 * @returns {Buffer} PNG file bytes, cropped to a square.
 */
function cropToSquarePng(pngBuffer) {
  const image = PNG.sync.read(pngBuffer);
  const side = Math.min(image.width, image.height);

  if (image.width === image.height) {
    return pngBuffer;
  }

  const offsetX = Math.floor((image.width - side) / 2);
  const offsetY = Math.floor((image.height - side) / 2);

  const cropped = new PNG({ width: side, height: side });

  for (let y = 0; y < side; y++) {
    const srcRowStart = ((offsetY + y) * image.width + offsetX) * 4;
    const dstRowStart = y * side * 4;
    image.data.copy(cropped.data, dstRowStart, srcRowStart, srcRowStart + side * 4);
  }

  return PNG.sync.write(cropped);
}

/**
 * Builds a tiny solid-color square PNG buffer. Useful for tests and for the
 * synthetic template fixture, where the exact pixels don't matter.
 *
 * @param {number} size Width and height in pixels.
 * @param {[number, number, number, number]} [rgba] Color, defaults to opaque gray.
 * @returns {Buffer}
 */
function makeSolidColorPng(size, rgba = [128, 128, 128, 255]) {
  const png = new PNG({ width: size, height: size });
  const [r, g, b, a] = rgba;

  for (let i = 0; i < size * size; i++) {
    const offset = i * 4;
    png.data[offset] = r;
    png.data[offset + 1] = g;
    png.data[offset + 2] = b;
    png.data[offset + 3] = a;
  }

  return PNG.sync.write(png);
}

module.exports = { cropToSquarePng, makeSolidColorPng };
