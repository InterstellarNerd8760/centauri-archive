"use strict";

const fs = require("node:fs");
const { createHash } = require("node:crypto");
const { TextDecoder } = require("node:util");
const { decodeRaster } = require("./photo_raster_independent.cjs");

const MAX_STREAM = 128 * 1024 * 1024;
const MAX_PAYLOAD = 16 * 1024 * 1024;
const names = ["", "mathematics", "photograph", "diagram", "vocabulary", "article",
  "reference", "attribution", "relationships", "recovery", "index", "specification"];
const byBytes = (a, b) => Buffer.compare(a, b);
const digest = bytes => createHash("sha256").update(bytes).digest();

function table(payload, stride) {
  if (payload.length < 4 || 4 + payload.readUInt32BE() * stride !== payload.length) {
    throw new Error("invalid table length");
  }
  const rows = [];
  for (let i = 4; i < payload.length; i += stride) rows.push(payload.subarray(i, i + stride));
  if (rows.some((row, index) => index > 0 && byBytes(rows[index - 1], row) >= 0)) {
    throw new Error("unordered table");
  }
  return rows;
}

function decode(data) {
  if (!data.length || data.length > MAX_STREAM) throw new Error("stream length");
  const records = [];
  let links = [];
  let indexRows = null;
  let cursor = 0;
  const text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });
  while (cursor < data.length) {
    if (data.length - cursor < 16 || data.readUInt32BE(cursor) !== 0xca1c662a ||
        data[cursor + 4] !== 1 || data[cursor + 7] !== 0) throw new Error("frame header");
    const kind = data[cursor + 5];
    const layer = data[cursor + 6];
    const id = data.readUInt32BE(cursor + 8);
    const bytes = data.readUInt32BE(cursor + 12);
    const end = cursor + 16 + bytes;
    if (!names[kind] || layer > 5 || id <= (records.at(-1)?.id ?? 0) ||
        id === 0xffffffff || bytes < 1 || bytes > MAX_PAYLOAD || end + 32 > data.length) {
      throw new Error("frame fields");
    }
    if (!digest(data.subarray(cursor, end)).equals(data.subarray(end, end + 32))) {
      throw new Error("frame digest");
    }
    const payload = data.subarray(cursor + 16, end);
    if (kind === 2) {
      if (decodeRaster(payload).recordId !== id) throw new Error("nested raster identifier");
    } else if (kind === 8) {
      links = links.concat(table(payload, 9).map(row => [
        row.readUInt32BE(0), row.readUInt32BE(4), row[8],
      ]));
    } else if (kind === 10) {
      if (indexRows !== null) throw new Error("duplicate index");
      indexRows = table(payload, 10).map(row => [
        row.readUInt32BE(), row[4], row[5], row.readUInt32BE(6),
      ]);
    } else if (payload.includes(0) || !/[^\x09-\x0d\x20]/.test(text.decode(payload))) {
      throw new Error("invalid text");
    }
    records.push({ id, type: names[kind], kind, layer, bytes, sha256: digest(payload).toString("hex") });
    cursor = end + 32;
  }
  const layers = new Map(records.map(record => [record.id, record.layer]));
  const dependent = new Map(records.map(({ id }) => [id, []]));
  const pending = new Map(records.map(({ id }) => [id, 0]));
  for (const [source, target, role] of links) {
    if (!layers.has(source) || !layers.has(target) || source === target ||
        role < 1 || role > 5 || (role === 1 && layers.get(target) > layers.get(source))) {
      throw new Error("invalid relationship");
    }
    if (role === 1) {
      dependent.get(target).push(source);
      pending.set(source, pending.get(source) + 1);
    }
  }
  const roots = records.map(record => record.id).filter(id => pending.get(id) === 0);
  for (let index = 0; index < roots.length; index++) {
    for (const id of dependent.get(roots[index])) {
      const outstanding = pending.get(id) - 1;
      pending.set(id, outstanding);
      if (outstanding === 0) roots.push(id);
    }
  }
  if (roots.length !== records.length) throw new Error("cyclic prerequisites");
  const expected = records.filter(record => record.kind !== 10)
    .map(({ id, kind, layer, bytes }) => [id, kind, layer, bytes]);
  if (indexRows && JSON.stringify(indexRows) !== JSON.stringify(expected)) {
    throw new Error("index disagrees with verified records");
  }
  return { records, index: indexRows ? "consistent" : "missing" };
}

if (require.main === module) {
  try {
    const [, , file, ...extra] = process.argv;
    if (!file || extra.length || fs.statSync(file).size > MAX_STREAM) {
      throw new Error("usage: node tools/research_archive_independent.cjs FILE");
    }
    process.stdout.write(JSON.stringify(decode(fs.readFileSync(file))) + "\n");
  } catch (error) {
    process.stderr.write(`research archive: ${error.message}\n`);
    process.exitCode = 1;
  }
}

module.exports = { decode };
