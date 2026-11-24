"use strict";
// Independent implementation of docs/raw-raster-experiment.md; no Python dependency.
function decodeRawRaster(bytes) {
  const sync = [255,0,255,0,0,255,0,255];
  if (!(bytes instanceof Uint8Array) || bytes.length < 13 || sync.some((v,i)=>bytes[i]!==v) || bytes[8]!==1) throw new Error("invalid header");
  const width=bytes[9]*256+bytes[10], height=bytes[11]*256+bytes[12];
  if(width<1||height<1||width>1024||height>1024) throw new Error("invalid dimensions");
  const count=width*height, size=Math.ceil(count/8);
  if(bytes.length!==13+size*2) throw new Error("invalid length");
  for(let i=0;i<size;i++) if(bytes[13+i]+bytes[13+size+i]!==255) throw new Error("complement mismatch");
  const pixels=[];
  for(let i=0;i<size;i++){
    let value=bytes[13+i];
    for(let weight=128;weight>=1;weight/=2){
      const bit=Number(value>=weight);
      if(bit)value-=weight;
      if(pixels.length<count)pixels.push(bit);
      else if(bit)throw new Error("nonzero padding");
    }
  }
  return {width,height,pixels};
}
if (typeof module !== "undefined") module.exports = {decodeRawRaster};
