"use strict";

/**
 * RLE2: the run-length-encoded DXT5 texture format (resource type 0x3453CF95)
 * the game uses for CAS Part diffuse textures. Ported from s4pi's
 * RLEResource.cs (s4ptacle/Sims4Tools), RLE2 branch only.
 *
 * Layout: 16-byte header (FourCC "DXT5", version "RLE2", width, height,
 * mip count, 0), then one 20-byte mip header per mip (offsets of the
 * command stream and of blocks 2, 3, 0 and 1), then the command stream and
 * the four block streams. Each DXT5 block (16 bytes) is split into
 * block0 = alpha endpoints (2 bytes), block1 = alpha indices (6),
 * block2 = color endpoints (4), block3 = color indices (4). Commands are
 * uint16 `count << 2 | op`: op 0 = fully transparent blocks (no data),
 * op 2 = fully opaque blocks (only blocks 2 and 3 stored), op 1 = the rest.
 */

const DXT5_FOURCC = 0x35545844; // "DXT5"
const RLE2_VERSION = 0x32454c52; // "RLE2"
const DDS_HEADER_SIZE = 128;
const MAX_RUN = 0x3fff;

const FULL_TRANSPARENT_BLOCK = Buffer.from([
  0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
]);
const FULL_OPAQUE_ALPHA = Buffer.from([0x00, 0x05, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]);

/** The 16 alpha values of a DXT5 block (same palette rules as s4pi's UnpackAlpha). */
function blockAlphas(data, offset) {
  const a0 = data[offset];
  const a1 = data[offset + 1];
  const palette = [a0, a1];
  if (a0 > a1) {
    for (let i = 1; i <= 6; i++) palette.push(Math.floor(((7 - i) * a0 + i * a1 + 3) / 7));
  } else {
    for (let i = 1; i <= 4; i++) palette.push(Math.floor(((5 - i) * a0 + i * a1 + 2) / 5));
    palette.push(0x00, 0xff);
  }
  let bits = 0n;
  for (let i = 7; i >= 2; i--) bits = (bits << 8n) | BigInt(data[offset + i]);
  const alphas = [];
  for (let i = 0; i < 16; i++) {
    alphas.push(palette[Number(bits & 7n)]);
    bits >>= 3n;
  }
  return alphas;
}

function mipBlockBytes(width, height, mipIndex) {
  const w = Math.max(4, width >> mipIndex);
  const h = Math.max(4, height >> mipIndex);
  return Math.max(1, Math.floor((w + 3) / 4)) * Math.max(1, Math.floor((h + 3) / 4)) * 16;
}

/**
 * Encodes an unshuffled DXT5 .dds file (with its mip chain) as RLE2.
 *
 * @param {Buffer} dds Full DDS file bytes (magic + 124-byte header + data).
 * @returns {Buffer}
 */
function encodeRle2FromDds(dds) {
  if (dds.readUInt32LE(84) !== DXT5_FOURCC) throw new Error("RLE2: o DDS precisa ser DXT5 sem shuffle");
  const height = dds.readUInt32LE(12);
  const width = dds.readUInt32LE(16);
  const mipCount = Math.max(1, dds.readUInt32LE(28));

  const commands = [];
  const blocks = [[], [], [], []];
  const sizes = [0, 0, 0, 0];
  const mipHeaders = [];
  let commandBytes = 0;
  const push = (i, buf) => {
    blocks[i].push(buf);
    sizes[i] += buf.length;
  };

  let pos = DDS_HEADER_SIZE;
  for (let mip = 0; mip < mipCount; mip++) {
    mipHeaders.push({ command: commandBytes, b2: sizes[2], b3: sizes[3], b0: sizes[0], b1: sizes[1] });
    const size = mipBlockBytes(width, height, mip);
    const data = dds.subarray(pos, pos + size);
    pos += size;
    const kind = (off) => {
      const alphas = blockAlphas(data, off);
      if (alphas.every((a) => a === 0)) return 0;
      if (alphas.every((a) => a === 0xff)) return 2;
      return 1;
    };
    for (let off = 0; off < size; ) {
      const op = kind(off);
      let count = 0;
      while (count < MAX_RUN && off < size && kind(off) === op) {
        if (op === 2) {
          push(2, data.subarray(off + 8, off + 12));
          push(3, data.subarray(off + 12, off + 16));
        } else if (op === 1) {
          push(0, data.subarray(off, off + 2));
          push(1, data.subarray(off + 2, off + 8));
          push(2, data.subarray(off + 8, off + 12));
          push(3, data.subarray(off + 12, off + 16));
        }
        count++;
        off += 16;
      }
      const cmd = Buffer.alloc(2);
      cmd.writeUInt16LE((count << 2) | op);
      commands.push(cmd);
      commandBytes += 2;
    }
  }

  const header = Buffer.alloc(16 + 20 * mipCount);
  header.writeUInt32LE(DXT5_FOURCC, 0);
  header.writeUInt32LE(RLE2_VERSION, 4);
  header.writeUInt16LE(width, 8);
  header.writeUInt16LE(height, 10);
  header.writeUInt16LE(mipCount, 12);
  header.writeUInt16LE(0, 14);
  const commandStart = header.length;
  const b2Start = commandStart + commandBytes;
  const b3Start = b2Start + sizes[2];
  const b0Start = b3Start + sizes[3];
  const b1Start = b0Start + sizes[0];
  mipHeaders.forEach((m, i) => {
    const at = 16 + 20 * i;
    header.writeInt32LE(m.command + commandStart, at);
    header.writeInt32LE(m.b2 + b2Start, at + 4);
    header.writeInt32LE(m.b3 + b3Start, at + 8);
    header.writeInt32LE(m.b0 + b0Start, at + 12);
    header.writeInt32LE(m.b1 + b1Start, at + 16);
  });
  return Buffer.concat([header, ...commands, ...blocks[2], ...blocks[3], ...blocks[0], ...blocks[1]]);
}

/**
 * Decodes RLE2 back into raw DXT5 block data (all mips concatenated).
 *
 * @param {Buffer} rle
 * @returns {{width: number, height: number, mipCount: number, blocks: Buffer}}
 */
function decodeRle2(rle) {
  if (rle.readUInt32LE(0) !== DXT5_FOURCC || rle.readUInt32LE(4) !== RLE2_VERSION) {
    throw new Error("não é uma textura RLE2");
  }
  const width = rle.readUInt16LE(8);
  const height = rle.readUInt16LE(10);
  const mipCount = rle.readUInt16LE(12);
  const mips = [];
  for (let i = 0; i < mipCount; i++) {
    const at = 16 + 20 * i;
    mips.push({
      command: rle.readInt32LE(at),
      b2: rle.readInt32LE(at + 4),
      b3: rle.readInt32LE(at + 8),
      b0: rle.readInt32LE(at + 12),
      b1: rle.readInt32LE(at + 16),
    });
  }
  // sentinel: the end of each stream is the start of the next one
  mips.push({ command: mips[0].b2, b2: mips[0].b3, b3: mips[0].b0, b0: mips[0].b1, b1: rle.length });

  const out = [];
  for (let i = 0; i < mipCount; i++) {
    let { b0, b1, b2, b3 } = mips[i];
    for (let c = mips[i].command; c < mips[i + 1].command; c += 2) {
      const command = rle.readUInt16LE(c);
      const op = command & 3;
      const count = command >> 2;
      for (let j = 0; j < count; j++) {
        if (op === 0) {
          out.push(FULL_TRANSPARENT_BLOCK);
        } else if (op === 1) {
          out.push(rle.subarray(b0, b0 + 2), rle.subarray(b1, b1 + 6), rle.subarray(b2, b2 + 4), rle.subarray(b3, b3 + 4));
          b0 += 2;
          b1 += 6;
          b2 += 4;
          b3 += 4;
        } else if (op === 2) {
          out.push(FULL_OPAQUE_ALPHA, rle.subarray(b2, b2 + 4), rle.subarray(b3, b3 + 4));
          b2 += 4;
          b3 += 4;
        } else {
          throw new Error("RLE2: comando inválido " + op);
        }
      }
    }
  }
  return { width, height, mipCount, blocks: Buffer.concat(out) };
}

module.exports = { RLE2_RESOURCE_TYPE: 0x3453cf95, encodeRle2FromDds, decodeRle2, blockAlphas };
