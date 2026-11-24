"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { webcrypto } = require("node:crypto");
const { decodeIntactProtection, decodeRaster, renderSamples } = require("../website/visual-explainers.js");
const { decodeRaster: decodeReference, previewRaster } = require("../tools/photo_raster_independent.cjs");

async function main() {
  const directory = path.join(__dirname, "../website/photo-reconstruction");
  const manifest = JSON.parse(fs.readFileSync(path.join(directory, "manifest.json"), "utf8"));
  let count = 0;
  for (const record of manifest.records) {
    for (const variant of record.variants) {
      const original = fs.readFileSync(path.join(directory, variant.file));
      const frame = await decodeRaster(original, webcrypto.subtle);
      const decoded = decodeReference(original);
      assert.equal(frame.recordId, decoded.recordId, variant.file);
      assert.equal(frame.width, decoded.width, variant.file);
      assert.equal(frame.height, decoded.height, variant.file);
      assert.deepEqual(frame.payload, decoded.payload, variant.file);

      const samples = previewRaster(decoded);
      const raster = samples.subarray(Buffer.byteLength(`P5\n${frame.width} ${frame.height}\n255\n`));
      const actual = renderSamples(frame);
      const expected = Buffer.alloc(frame.width * frame.height * 4, 255);
      for (let i = 0; i < frame.width * frame.height; i += 1) {
        const rgb = variant.mode === "rgb" ? raster.subarray(i * 3, i * 3 + 3) : [raster[i], raster[i], raster[i]];
        expected.set(rgb, i * 4);
      }
      assert.deepEqual(Buffer.from(actual), expected, variant.file);
      count += 1;
    }
  }

  const rgb = fs.readFileSync(path.join(directory, manifest.protection.raw));
  await assert.rejects(decodeRaster(rgb.subarray(0, -1), webcrypto.subtle), /length/);
  const damaged = Buffer.from(rgb);
  damaged[22] ^= 1;
  await assert.rejects(decodeRaster(damaged, webcrypto.subtle), /SHA-256/);
  const protectedCopy = fs.readFileSync(path.join(directory, manifest.protection.file));
  const unwrapped = await decodeIntactProtection(protectedCopy, manifest.protection, webcrypto.subtle);
  assert.deepEqual(Buffer.from(unwrapped), rgb);
  const damagedCopy = Buffer.from(protectedCopy);
  damagedCopy[254] ^= 1;
  await assert.rejects(decodeIntactProtection(damagedCopy, manifest.protection, webcrypto.subtle), /published inventory/);
  console.log(`Verified browser pixel reconstruction against the independent Node decoder for ${count} frames.`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
