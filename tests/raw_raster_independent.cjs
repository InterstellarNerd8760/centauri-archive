"use strict";
const assert = require("node:assert/strict");
const {decodeRawRaster} = require("../tools/raw_raster_independent.cjs");
const sample = Uint8Array.from(Buffer.from("ff00ff0000ff00ff010008000810387cfe18181801efc78301e7e7e7fe","hex"));
const expected = "0001000000111000011111001111111000011000000110000001100000000001";
const result = decodeRawRaster(sample);
assert.equal(result.width,8); assert.equal(result.height,8);
assert.equal(result.pixels.join(""),expected);
for(let i=13;i<sample.length;i++) for(let bit=0;bit<8;bit++){
  const changed=sample.slice(); changed[i]^=1<<bit;
  assert.throws(()=>decodeRawRaster(changed));
}
assert.throws(()=>decodeRawRaster(sample.slice(0,-1)));
assert.throws(()=>decodeRawRaster(Uint8Array.from([...sample,0])));
const small = Uint8Array.from(Buffer.from("ff00ff0000ff00ff0100030001a05f","hex"));
assert.deepEqual(decodeRawRaster(small),{width:3,height:1,pixels:[1,0,1]});
const badPadding=small.slice();badPadding[13]=161;badPadding[14]=94;
assert.throws(()=>decodeRawRaster(badPadding));
const commonMode=sample.slice();commonMode[13]^=128;commonMode[21]^=128;
assert.notEqual(decodeRawRaster(commonMode).pixels.join(""),expected);
console.log("Independent raster checks passed; common-mode corruption remains undetectable.");
