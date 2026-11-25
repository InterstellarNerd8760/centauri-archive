"use strict";

// Independent Node implementation of docs/raw-raster-v2.md.
const { createHash, timingSafeEqual } = require("node:crypto");
const fs = require("node:fs");

const HEADER = 22;
const DIGEST = 32;
const LIMIT = 16384;
const MAX_PIXELS = 16777216;
const MAX_FRAME_BYTES = HEADER + 3 * MAX_PIXELS + DIGEST;
const MARKER = Buffer.from([255, 0, 255, 0, 0, 255, 0, 255]);

function decodeRaster(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length < HEADER + DIGEST) {
    throw new Error("truncated frame");
  }
  const frame = Buffer.from(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (!frame.subarray(0, 8).equals(MARKER) || frame[8] !== 2) {
    throw new Error("invalid marker or version");
  }
  const mode = frame[9];
  const width = frame.readUInt16BE(10);
  const height = frame.readUInt16BE(12);
  const recordId = frame.readUInt32BE(14);
  const declaredLength = frame.readUInt32BE(18);
  const pixels = width * height;
  if (![1, 8, 24].includes(mode)) {
    throw new Error("invalid raster mode");
  }
  if (width === 0 || height === 0 || width > LIMIT || height > LIMIT
      || pixels > MAX_PIXELS || recordId === 0) {
    throw new Error("invalid dimensions or identifier");
  }
  const payloadBytes = Math.ceil(pixels * mode / 8);
  const digestOffset = HEADER + payloadBytes;
  if (declaredLength !== payloadBytes || frame.length !== digestOffset + DIGEST) {
    throw new Error("frame length mismatch");
  }
  const payload = frame.subarray(HEADER, digestOffset);
  if (mode === 1 && pixels % 8) {
    const unusedMask = (1 << (8 - pixels % 8)) - 1;
    if (payload[payloadBytes - 1] & unusedMask) {
      throw new Error("nonzero padding");
    }
  }
  const calculatedDigest = createHash("sha256").update(frame.subarray(0, digestOffset)).digest();
  if (!timingSafeEqual(calculatedDigest, frame.subarray(digestOffset))) {
    throw new Error("SHA-256 mismatch");
  }
  return { width, height, recordId, mode, payload: Buffer.from(payload) };
}

function previewRaster({ width, height, mode, payload }) {
  const header = Buffer.from(`${mode === 24 ? "P6" : "P5"}\n${width} ${height}\n255\n`, "ascii");
  if (mode !== 1) {
    return Buffer.concat([header, payload]);
  }
  const samples = Buffer.alloc(width * height);
  for (let index = 0; index < samples.length; index += 1) {
    const byte = payload[Math.floor(index / 8)];
    const weight = 128 / (2 ** (index % 8));
    samples[index] = 255 * (Math.floor(byte / weight) % 2);
  }
  return Buffer.concat([header, samples]);
}

if (require.main === module) {
  try {
    const [source, ...extra] = process.argv.slice(2);
    if (!source || extra.length) {
      throw new Error("usage: node tools/photo_raster_independent.cjs FRAME > PREVIEW");
    }
    if (fs.statSync(source).size > MAX_FRAME_BYTES) {
      throw new Error("frame exceeds supported byte limit");
    }
    process.stdout.write(previewRaster(decodeRaster(fs.readFileSync(source))));
  } catch (error) {
    console.error(`photo-raster: ${error.message}`);
    process.exitCode = 1;
  }
}

module.exports = { decodeRaster, previewRaster };
