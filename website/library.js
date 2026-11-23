/* Browser-only presentation layer. Archive payload bytes remain unchanged. */
"use strict";

const groups = [
  ["earth", "01 / Earth & the Solar System"],
  ["biology", "02 / The living world"],
  ["humanity", "03 / Human civilization"],
  ["primer", "04 / Reading experiments"],
  ["messages", "05 / Messages"],
];
const descriptions = {
  "earth/solar-system.txt": ["The Solar System", "Our star, its planets and Earth's place among them."],
  "earth/water.txt": ["Water on Earth", "An essential chemical compound and its role on Earth."],
  "biology/foundations.txt": ["What life is", "Cells, chemistry, metabolism and common ancestry."],
  "biology/genetics.txt": ["DNA and inheritance", "How information is transmitted through living generations."],
  "biology/diversity.txt": ["The diversity of life", "Bacteria, archaea, eukaryotes and ecosystems."],
  "humanity/civilization.txt": ["Human civilization", "Our social lives, languages, traditions and technologies."],
  "humanity/history.txt": ["A short human history", "Selected turning points across a much longer history."],
  "primer/start.txt": ["Start with the assumptions", "What this human-readable development edition requires."],
  "primer/mathematics.txt": ["Counting and mathematics", "Foundations for a future mathematical primer."],
  "primer/format.txt": ["Current digital format", "Why ZIP, UTF-8 and SHA-256 do not solve decoding."],
  "primer/raster-example.txt": ["Eight-by-eight image", "A tiny example of binary symbols becoming pixels."],
  "messages/draft.txt": ["A message draft", "An unapproved individual editorial placeholder."]
};
const $ = (id) => document.getElementById(id);
let records = [], activeIndex = -1;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (typeof text === "string") element.textContent = text;
  if (className) element.className = className;
  return element;
}
function clear(element) { element.replaceChildren(); }
function titleFor(path) {
  return descriptions[path] || [path.split("/").pop().replace(".txt", "").replace(/-/g, " "), "Original archive record"];
}
function renderBody(raw, path) {
  const target = $("reader-content");
  clear(target);
  if (path === "primer/raster-example.txt") {
    target.append(node("p", "This raw example represents an 8 × 8 grid. Each line holds eight binary symbols. The interpretation is not self-evident without a primer."));
    target.append(node("pre", raw, "reader-code"));
    return;
  }
  const parts = raw.trim().split(/\n\s*\n/);
  for (let index = 0; index < parts.length; index++) {
    const lines = parts[index].split(/\n/).map((line) => line.trim()).filter(Boolean);
    if (!lines.length) continue;
    if (index === 0 && lines.length === 1 && lines[0] === lines[0].toUpperCase()) continue;
    if (lines.every((line) => line.startsWith("- "))) {
      const list = node("ul");
      lines.forEach((line) => list.append(node("li", line.slice(2))));
      target.append(list);
    } else if (lines.length === 1 && lines[0] === lines[0].toUpperCase() && lines[0].length < 90) {
      target.append(node("h3", lines[0]));
    } else {
      target.append(node("p", lines.join(" ")));
    }
  }
}
function renderNav(filter = "") {
  const nav = $("record-nav");
  clear(nav);
  const query = filter.trim().toLowerCase();
  let shown = 0;
  groups.forEach(([category, label]) => {
    const subset = records.filter((record) => record.path.startsWith(category + "/") &&
      (record.title + " " + record.description + " " + record.path).toLowerCase().includes(query));
    if (!subset.length) return;
    nav.append(node("p", label, "reader-chapter"));
    subset.forEach((record) => {
      const button = node("button", record.title, "record-nav-link");
      button.type = "button";
      button.dataset.path = record.path;
      button.setAttribute("aria-current", records[activeIndex]?.path === record.path ? "page" : "false");
      button.addEventListener("click", () => showRecord(record.path, true));
      nav.append(button);
      shown += 1;
    });
  });
  if (!shown) nav.append(node("p", "No matching records.", "reader-loading"));
}
async function showRecord(path, updateAddress = false) {
  const index = records.findIndex((item) => item.path === path);
  if (index < 0) return;
  activeIndex = index;
  const record = records[index];
  $("record-title").textContent = record.title;
  $("record-summary").textContent = record.description;
  $("record-category").textContent = record.group;
  $("record-count").textContent = (index + 1) + " / " + records.length;
  $("record-raw").href = "records/" + record.path;
  $("record-prev").disabled = index === 0;
  $("record-next").disabled = index === records.length - 1;
  clear($("reader-content"));
  $("reader-content").append(node("p", "Loading the record…", "reader-loading"));
  renderNav($("library-search").value);
  if (updateAddress) {
    const url = new URL(window.location.href);
    url.searchParams.set("record", record.path);
    window.history.pushState({}, "", url);
  }
  try {
    const response = await fetch("records/" + record.path);
    if (!response.ok) throw new Error("Record not found");
    const raw = await response.text();
    if (index === activeIndex) renderBody(raw, record.path);
  } catch (error) {
    if (index === activeIndex) {
      clear($("reader-content"));
      $("reader-content").append(node("p", "Unable to read this file. The downloadable archive remains available."));
    }
  }
}
async function init() {
  try {
    const response = await fetch("downloads/manifest.json");
    if (!response.ok) throw new Error("Manifest not available");
    const manifest = await response.json();
    const files = Array.isArray(manifest.files) ? manifest.files : [];
    const byGroup = new Map(groups.map(([key]) => [key, []]));
    files.forEach((file) => {
      if (!file.path?.startsWith("content/") || file.media_type !== "text/plain") return;
      const path = file.path.slice("content/".length);
      const group = groups.find(([key]) => path.startsWith(key + "/"));
      if (!group) return;
      const [title, description] = titleFor(path);
      byGroup.get(group[0]).push({path, title, description, group: group[1]});
    });
    records = groups.flatMap(([key]) => byGroup.get(key).sort((a, b) => a.title.localeCompare(b.title)));
    if (!records.length) throw new Error("No records");
    const selected = new URL(window.location.href).searchParams.get("record");
    renderNav();
    await showRecord(records.some((r) => r.path === selected) ? selected : "earth/solar-system.txt");
  } catch (error) {
    $("record-nav").textContent = "Could not load the index. Download the archive using the home page.";
  }
}
$("library-search").addEventListener("input", (event) => renderNav(event.target.value));
$("record-prev").addEventListener("click", () => records[activeIndex - 1] && showRecord(records[activeIndex - 1].path, true));
$("record-next").addEventListener("click", () => records[activeIndex + 1] && showRecord(records[activeIndex + 1].path, true));
window.addEventListener("popstate", () => {
  const selected = new URL(window.location.href).searchParams.get("record");
  if (selected) showRecord(selected);
});
init();
