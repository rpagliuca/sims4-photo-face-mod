"use strict";

const { PNG } = require("pngjs");

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

/**
 * Where the photo goes in the 1024x2048 atlas the game composes for each Sim:
 * the glasses region the CASP template's quad is UV-mapped to (see
 * packages/casp_template/README.md).
 */
const ATLAS = { width: 1024, height: 2048 };
const PHOTO_RECT = { x: 512, y: 128, width: 256, height: 128 };

/** Width/height of the plate in the game (22 x 28 cm): the photo is cropped to it. */
const PLATE_ASPECT = 0.22 / 0.28;

/**
 * Center-crops an image (pngjs object) to the given width/height ratio.
 *
 * @param {PNG} image
 * @param {number} aspect
 * @returns {{x: number, y: number, width: number, height: number}}
 */
function centerCropRect(image, aspect) {
  if (image.width / image.height > aspect) {
    const width = Math.round(image.height * aspect);
    return { x: Math.floor((image.width - width) / 2), y: 0, width, height: image.height };
  }
  const height = Math.round(image.width / aspect);
  return { x: 0, y: Math.floor((image.height - height) / 2), width: image.width, height };
}

/**
 * Builds the full 1024x2048 RGBA atlas PNG for one photo: transparent
 * everywhere except PHOTO_RECT, which gets the photo cropped to the plate's
 * aspect and squeezed into the 256x128 rectangle (nearest neighbour - the
 * quad stretches it back; low resolution is part of the tosco look).
 *
 * @param {Buffer} pngBuffer Raw PNG file bytes of the photo.
 * @returns {Buffer} PNG file bytes of the atlas.
 */
function buildFaceAtlasPng(pngBuffer) {
  const photo = PNG.sync.read(pngBuffer);
  const crop = centerCropRect(photo, PLATE_ASPECT);
  const atlas = new PNG({ width: ATLAS.width, height: ATLAS.height });
  atlas.data.fill(0);
  for (let y = 0; y < PHOTO_RECT.height; y++) {
    const sy = crop.y + Math.min(crop.height - 1, Math.floor(((y + 0.5) * crop.height) / PHOTO_RECT.height));
    for (let x = 0; x < PHOTO_RECT.width; x++) {
      const sx = crop.x + Math.min(crop.width - 1, Math.floor(((x + 0.5) * crop.width) / PHOTO_RECT.width));
      const src = (sy * photo.width + sx) * 4;
      const dst = ((PHOTO_RECT.y + y) * ATLAS.width + PHOTO_RECT.x + x) * 4;
      photo.data.copy(atlas.data, dst, src, src + 3);
      atlas.data[dst + 3] = 255; // the plate is always opaque
    }
  }
  return PNG.sync.write(atlas);
}

module.exports = {
  ATLAS,
  PHOTO_RECT,
  PLATE_ASPECT,
  buildFaceAtlasPng,
  centerCropRect,
  makeSolidColorPng,
};
