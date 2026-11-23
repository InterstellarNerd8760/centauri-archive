# Experimental raw-raster frame, version 1

**Status: software interoperability test, not a flight format or evidence of extraterrestrial readability.**

Purpose: reconstruct one monochrome image without a ZIP reader, JSON parser, UTF-8 text, JPEG codec, or webpage. A physical primer still has to demonstrate all these conventions using observable examples.

## Byte layout

| Position | Bytes | Interpretation |
| --- | ---: | --- |
| 0–7 | 8 | Fixed sync marker, hexadecimal FF 00 FF 00 00 FF 00 FF |
| 8 | 1 | Version, presently 01 |
| 9–10 | 2 | Width as unsigned big-endian integer, 1–1024 |
| 11–12 | 2 | Height as unsigned big-endian integer, 1–1024 |
| 13 onward | ceil(width × height / 8) | Pixels packed MSB-first, row-by-row, starting top-left |
| Remaining bytes | Same as pixel bytes | Bitwise complement of each pixel byte, to detect some damage |

One pixel is either 0 (black) or 1 (white). Its first value occupies bit 7 of the first payload byte. Next values occupy bits 6 through 0; then proceed to the next byte. Unused low bits in the final payload byte are zero; their complemented partners are therefore one. The decoder rejects extra or missing bytes and rejects any disagreement between each pixel byte and its complement.

The complement does **not** correct errors; simultaneous matching changes in both sections can evade detection. The sync sequence is not a universal recognition signal. Big-endian integers, bit order, corners, frame boundaries, color mapping and pixel dimensions are human-made conventions requiring physically evident demonstrations.

## Fixed test vector

Input: eight rows, each eight cells, in the existing source file archive/primer/raster-example.txt.

```text
00010000
00111000
01111100
11111110
00011000
00011000
00011000
00000001
```

Expected complete 29-byte binary frame (hexadecimal groups shown only to help human developers):

```text
ff00ff0000ff00ff 01 0008 0008
10387cfe18181801
efc78301e7e7e7fe
```

The last eight bytes are the bitwise complement of the eight pixel bytes. The decoded preview is exactly 8 × 8 pixels; there is no JPEG compression, external data dependency or accompanying English metadata in this frame.

## Reproduction

```sh
python3 tools/raw_raster.py encode archive/primer/raster-example.txt build/example.bin
python3 tools/raw_raster.py decode build/example.bin build/example.pgm
python3 -m unittest discover -s tests -v
```

Both the text-grid source and PGM output are **human-side teaching fixtures**. The binary frame is independently parseable using the byte layout above, and the tests check a hard-coded expected vector without deriving it from the decoder. That still does not demonstrate an independent second-language implementation or a physically self-explaining artifact.

## Next experiments

1. Print or etch a text-free physical key pairing an asymmetric 8 × 8 image with its ordered two-state pattern.
2. Conduct blind human decoding trials with no oral hints, separately scoring orientation, bit meaning, framing and scan order.
3. Create a truly independent implementation in a second language, using only this specification.
4. Quantify failures under truncation, bit flips and missing regions, then design an actual error-correcting scheme.
5. Decide how the raw frame might be recovered from a durable physical medium independently of modern computers.

Nothing in this format guarantees that an unfamiliar intelligence could infer its meaning. It is deliberately small so assumptions can be exposed and tested.
