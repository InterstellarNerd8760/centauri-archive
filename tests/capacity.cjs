'use strict';

const assert = require('node:assert/strict');
const { estimateCapacity } = require('../website/capacity.js');

const defaultInput = {
  logicalMB: 100, correction: 15, copies: 2,
  width: 40, height: 40, thickness: 1, density: 2.2,
  pitch: 10, planes: 1, usable: 70, shieldThickness: 0.5, shieldDensity: 2.7, mount: 5,
};
const result = estimateCapacity(defaultInput);
assert.equal(result.rawBytes, 1_400_000);
assert.equal(result.logicalBytes, 100_000_000);
assert.equal(result.correctionBytes, 15_000_000);
assert.equal(result.protectedBytes, 115_000_000);
assert.equal(result.redundancyBytes, 115_000_000);
assert.equal(result.totalBytes, 230_000_000);
assert.equal(result.substrateVolume, 1.6);
assert.ok(Math.abs(result.copyMass - 5.68) < 1e-10);
assert.ok(Math.abs(result.carrierMass - 16.36) < 1e-10);

const minimal = estimateCapacity({ ...defaultInput, logicalMB: 0.000001, correction: 0.1, copies: 1,
  width: 9, height: 9, pitch: 4000, planes: 2, usable: 100, shieldThickness: 0, mount: 0 });
assert.equal(minimal.rawBytes, 1);
assert.equal(minimal.logicalBytes, 1);
assert.equal(minimal.correctionBytes, 1);
assert.equal(minimal.totalBytes, 2);
assert.equal(minimal.redundancyBytes, 0);
assert.equal(minimal.copyMass, minimal.carrierMass);

const layered = estimateCapacity({ ...defaultInput, logicalMB: 64_000, planes: 5, copies: 3 });
assert.equal(layered.rawBytes, 7_000_000);
assert.equal(layered.protectedBytes, 73_600_000_000);
assert.equal(layered.totalBytes, 220_800_000_000);

const limits = estimateCapacity({ ...defaultInput, width: 1000, height: 1000, pitch: 0.2,
  planes: 100, usable: 99.9, logicalMB: 1_000_000, correction: 999.9, copies: 8 });
assert.equal(limits.rawBytes, 312_187_500_000_000);
assert.equal(limits.correctionBytes, 9_999_000_000_000);
assert.equal(limits.totalBytes, 87_992_000_000_000);
console.log('Capacity model: default, fractional-byte rounding, Extended and valid boundary examples passed');

const { contentMix } = require('../website/knowledge-capacity.js');
assert.deepEqual(contentMix({ articles: 3, articleBytes: 12, photos: 2, edge: 3,
  depth: 1, primer: 9, vocabulary: 5, metadata: 7 }),
  { articles: 36, photographs: 112, logical: 169 });
const curated = estimateCapacity({ ...defaultInput, logicalMB: 44.5, protectedOverride: 85_400_000 });
assert.equal(curated.protectedBytes, 85_400_000);
assert.equal(curated.correctionBytes, 40_900_000);
assert.equal(curated.totalBytes, 170_800_000);
