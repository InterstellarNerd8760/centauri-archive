"use strict";
// Browser raster demonstration, not the canonical CAR encoder.
(() => {
  const source = document.getElementById("explain-photo-source");
  if (!source) return;
  const canvas = document.getElementById("explain-photo-raster");
  const context = canvas.getContext("2d", {willReadFrequently:true});
  const size = document.getElementById("explain-resolution");
  const mode = document.getElementById("explain-mode");
  const summary = document.getElementById("explain-raster-summary");
  const stream = document.getElementById("explain-raster-stream");
  function draw() {
    if (!context || !source.naturalWidth) return;
    const edge = Number(size.value);
    const factor = edge / Math.max(source.naturalWidth, source.naturalHeight);
    canvas.width = Math.max(1, Math.round(source.naturalWidth * factor));
    canvas.height = Math.max(1, Math.round(source.naturalHeight * factor));
    context.drawImage(source, 0, 0, canvas.width, canvas.height);
    const frame = context.getImageData(0, 0, canvas.width, canvas.height);
    const bytes = [];
    let packed = 0, used = 0;
    for (let i=0; i<frame.data.length; i+=4) {
      const r=frame.data[i], g=frame.data[i+1], b=frame.data[i+2];
      const gray=Math.round(.299*r+.587*g+.114*b);
      if (mode.value==="rgb") bytes.push(r,g,b);
      else {
        const bit = gray >= 128 ? 1 : 0;
        const display = mode.value==="mono" ? bit*255 : gray;
        frame.data[i]=frame.data[i+1]=frame.data[i+2]=display;
        if (mode.value==="gray") bytes.push(gray);
        else {
          packed = (packed<<1)|bit;
          if (++used===8) {bytes.push(packed); packed=used=0;}
        }
      }
    }
    if (used) bytes.push(packed<<(8-used));
    context.putImageData(frame,0,0);
    summary.textContent=canvas.width+" × "+canvas.height+" pixels · "+bytes.length.toLocaleString()+" payload bytes";
    stream.textContent=bytes.slice(0,12).map(v=>v.toString(2).padStart(8,"0")).join(" ")+" …";
    canvas.setAttribute("aria-label","Reconstructed "+mode.options[mode.selectedIndex].text+" preview, "+canvas.width+" by "+canvas.height+" pixels");
  }
  source.addEventListener("load", draw);
  source.addEventListener("error",()=>{summary.textContent="Source photograph unavailable.";});
  size.addEventListener("input",draw); mode.addEventListener("change",draw);
  if (source.complete) draw();
})();
