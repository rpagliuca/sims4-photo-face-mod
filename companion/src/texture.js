"use strict";

const { DdsImage } = require("@s4tk/images");
const { DdsImageResource } = require("@s4tk/models");

const { cropToSquarePng } = require("./png");

/**
 * Default DDS conversion options for the tosco billboard texture.
 *
 * shuffle: true -> DST5 compression, which is the format the game's CAS Part
 * texture slot expects (unshuffled DXT5 is rejected by the game as a CASP
 * texture). maxMipMaps: 1 -> skip mipmap chain generation entirely; a
 * deliberately-flat billboard photo has no business being minified nicely.
 */
const DEFAULT_DDS_OPTIONS = { shuffle: true, maxMipMaps: 1 };

/**
 * Converts a PNG buffer into a shuffled (DST) DdsImage, cropping to a
 * centered square first so non-square photos don't get stretched.
 *
 * @param {Buffer} pngBuffer Raw PNG file bytes.
 * @param {object} [options] Overrides for DDS conversion (shuffle, maxMipMaps).
 * @returns {Promise<import("@s4tk/images").DdsImage>}
 */
async function pngBufferToDdsImage(pngBuffer, options = {}) {
  const squarePng = cropToSquarePng(pngBuffer);
  return DdsImage.fromImageAsync(squarePng, { ...DEFAULT_DDS_OPTIONS, ...options });
}

/**
 * Converts a PNG buffer into a DdsImageResource ready to be placed into a
 * Package at the CAS Part texture resource key.
 *
 * @param {Buffer} pngBuffer Raw PNG file bytes.
 * @param {object} [options] Overrides for DDS conversion.
 * @returns {Promise<import("@s4tk/models").DdsImageResource>}
 */
async function pngBufferToTextureResource(pngBuffer, options = {}) {
  const image = await pngBufferToDdsImage(pngBuffer, options);
  return DdsImageResource.fromDdsImage(image, "dst");
}

module.exports = {
  DEFAULT_DDS_OPTIONS,
  pngBufferToDdsImage,
  pngBufferToTextureResource,
};
