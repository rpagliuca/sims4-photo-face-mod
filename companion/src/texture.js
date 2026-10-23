"use strict";

const { DdsImage } = require("@s4tk/images");
const { RawResource } = require("@s4tk/models");

const { buildFaceAtlasPng } = require("./png");
const { encodeRle2FromDds } = require("./rle2");

/**
 * Converts a photo into the CAS Part diffuse texture the game expects: the
 * 1024x2048 atlas (photo in the glasses region, transparent elsewhere),
 * compressed as DXT5 with its full mip chain and run-length encoded as
 * RLE2 - the same format Sims4Studio writes for CAS diffuse textures.
 *
 * @param {Buffer} pngBuffer Raw PNG file bytes of the photo.
 * @returns {Promise<Buffer>} RLE2 resource bytes.
 */
async function photoToRle2(pngBuffer) {
  const atlas = buildFaceAtlasPng(pngBuffer);
  const dds = await DdsImage.fromImageAsync(atlas, { shuffle: false });
  return encodeRle2FromDds(dds.buffer);
}

/**
 * @param {Buffer} pngBuffer
 * @returns {Promise<import("@s4tk/models").RawResource>}
 */
async function photoToTextureResource(pngBuffer) {
  return RawResource.from(await photoToRle2(pngBuffer));
}

module.exports = { photoToRle2, photoToTextureResource };
