"""Render C2 dual-scale primer panels and a separate held-out readout sheet."""
import argparse
import json
from pathlib import Path

from build_primer import DOCS, Panel


def tile(panel, x, y, pitch, rows):
    """Move the fiducial and every cell by the same geometric scaling."""
    width = len(rows[0])
    panel.path(f"M{x - pitch} {y - pitch}v{-pitch}h{(width + 2) * pitch}"
               f"v{(len(rows) + 3) * pitch}h{-(width + 2) * pitch}v{-len(rows) * pitch}",
               max(1, pitch / 10))
    panel.dot(x, y - pitch, pitch / 4)
    panel.dot(x + pitch, y - pitch, pitch / 7)
    for row, pattern in enumerate(rows):
        panel.bits(x, y + row * pitch, pattern, pitch)


def brackets(panel, x, y, pitch, count):
    panel.line(x, y, x + count * pitch, y)
    for index in range(count + 1):
        tick = x + index * pitch
        panel.line(tick, y - 4, tick, y + 4)


def pitch_reference(panel, data):
    panel.frame(16, 181, "F / Locate and inspect smaller marks")
    large, small = data["coarse_pitch"], data["fine_pitch"]
    for index, pattern in enumerate(("10110010", "01101100")):
        y = 63 + index * 64
        panel.bits(68, y, pattern, large)
        panel.bits(342, y + (large - small) / 2, pattern, small)
        panel.line(244, y + large / 2, 326, y + large / 2)
        brackets(panel, 68, y + 34, large, 1)
        brackets(panel, 342, y + 34, small, large // small)
        panel.line(88, y + 34, 333, y + 34, 1)
    panel.label(463, 78, "The same marks can occur at different pitches.")
    panel.label(463, 103, "Compare the spacing between consecutive boundaries.")
    panel.label(463, 142, "Four small cells occupy the width of one large cell.")
    panel.label(463, 167, "An enlargement preserves the order and number of marks.")


def site(panel, record, x, y, pitch):
    panel.rect(x, y, 159, 102)
    panel.value(x + 17, y + 10, record["locator"], width=4, size=12)
    tile_x, tile_y = x + 56, y + 56
    tile(panel, tile_x, tile_y, pitch, record["rows"])
    return tile_x, tile_y


def locate(panel, record, row, fine, coarse):
    x = 184
    y = 291 + row * 187
    panel.value(62, y + 21, record["locator"], size=13)
    panel.line(122, y + 27, x, y + 27)
    tile_x, tile_y = site(panel, record, x, y, fine)
    large_x, large_y = 566, y + 46
    panel.line(tile_x + 9 * fine, tile_y - 2 * fine,
               large_x - coarse, large_y - 2 * coarse)
    panel.line(tile_x + 9 * fine, tile_y + 4 * fine,
               large_x - coarse, large_y + 4 * coarse)
    panel.value(large_x, large_y - 66, record["locator"], size=13)
    tile(panel, large_x, large_y, coarse, record["rows"])
    for row_index, pattern in enumerate(record["rows"]):
        line_y = large_y + row_index * coarse
        panel.line(large_x + 9 * coarse, line_y + coarse / 2, 778, line_y + coarse / 2)
        panel.bits(792, line_y + 4, pattern, 10)


def render_training(data, annotated=False):
    panel = Panel(
        754, annotated, title="Centauri Archive decoding primer C2",
        description="Matched markers lead from the outer map to two target regions. "
                    "Each fine tile is paired with a fourfold enlarged view and a row-by-row transcription.",
    )
    pitch_reference(panel, data)
    panel.frame(213, 524, "Match the locator, enlarge the target, copy stable states")
    panel.label(62, 263, "Locator")
    panel.label(184, 263, "Target outline")
    panel.label(565, 263, "Enlarged view")
    panel.label(792, 263, "Ordered rows")
    for row, record in enumerate(data["training"]):
        locate(panel, record, row, data["fine_pitch"], data["coarse_pitch"])
    panel.label(62, 687, "The matching locator identifies each target. Follow the small frame and its unequal marks.")
    panel.label(62, 711, "If any mark remains unresolved, record that position as unknown.")
    return panel.render()


def render_trial(data):
    panel = Panel(330)
    panel.frame(16, 295, "")
    record = data["trial"]
    panel.value(81, 91, record["locator"], size=20)
    panel.line(183, 101, 401, 101)
    panel.rect(401, 57, 416, 216, "white")
    sites = (data["training"][1], record, data["training"][0])
    for index, candidate in enumerate(sites):
        x, y = (432, 80) if index == 0 else (625, 80 + (index - 1) * 91)
        panel.rect(x, y, 144, 75)
        panel.value(x + 12, y + 8, candidate["locator"], size=10)
        tile(panel, x + 71, y + 38, data["fine_pitch"], candidate["rows"])
    return panel.render()


def outputs(data):
    return {
        "primer-c2.svg": render_training(data),
        "primer-c2-annotated.svg": render_training(data, annotated=True),
        "primer-c2-trial.svg": render_trial(data),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DOCS)
    parser.add_argument("--check", action="store_true", help="check committed diagrams for drift")
    args = parser.parse_args()
    data = json.loads((DOCS / "primer-c2-data.json").read_text(encoding="utf-8"))
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, svg in outputs(data).items():
        path = args.output_dir / name
        if args.check:
            if not path.is_file() or path.read_bytes() != svg.encode("utf-8"):
                parser.error(f"stale or missing diagram: {path}")
        else:
            path.write_bytes(svg.encode("utf-8"))


if __name__ == "__main__":
    main()
