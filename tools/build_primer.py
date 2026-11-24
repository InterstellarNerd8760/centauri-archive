"""Render the structured Centauri primer C1 and its held-out trial sheet."""
import argparse
from html import escape
import json
from pathlib import Path


DOCS = Path(__file__).resolve().parents[1] / "docs"
WIDTH = 1000
GLYPHS = {
    "eq": "M-7 -3H7M-7 3H7",
    "lt": "M6 -7L-6 0L6 7",
    "add": "M-7 0H7M0 -7V7",
    "subtract": "M-7 0H7",
    "multiply": "M-6 -6L6 6M6 -6L-6 6",
    "divide": "M-7 0H7M0 -6h1M0 6h1",
    "unknown": "M0 -7L7 0L0 7L-7 0Z",
    "root": "M-9 0H-5L-1 7L4 -7H10",
}


class Panel:
    """Emit a small SVG using physical marks, with optional annotations."""

    def __init__(self, height, annotated=False):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}">'
        ]
        self.annotated = annotated
        if annotated:
            self.parts += [
                "<title>Centauri Archive decoding primer C1</title>",
                "<desc>Five experimental stages introduce physical marks, quantity, "
                "geometry, a hydrogen reference and toy raster frames.</desc>",
            ]
        self.rect(0, 0, WIDTH, height, "white", "none")

    def rect(self, x, y, width, height, fill="white", stroke="black"):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'fill="{fill}" stroke="{stroke}"/>'
        )

    def path(self, path, width=1.5, transform=""):
        self.parts.append(
            f'<path d="{path}" fill="none" stroke="black" '
            f'stroke-width="{width}" transform="{transform}"/>'
        )

    def line(self, x1, y1, x2, y2, width=1.5):
        self.path(f"M{x1} {y1}L{x2} {y2}", width)

    def dot(self, x, y, radius=3.5, fill="black"):
        self.parts.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="black"/>'
        )

    def label(self, x, y, label, size=14):
        if self.annotated:
            self.parts.append(
                f'<text x="{x}" y="{y}" font-family="sans-serif" '
                f'font-size="{size}">{escape(label)}</text>'
            )

    def glyph(self, x, y, name):
        self.path(GLYPHS[name], 2, f"translate({x} {y})")

    def frame(self, top, height, title):
        bottom = top + height
        self.path(f"M20 {top + 23}V{top}H980V{bottom}H20V{top + 40}", 2.5)
        self.dot(36, top + 15, 6)
        self.dot(51, top + 15, 3)
        self.label(74, top + 21, title, 18)

    def quantity(self, x, y, value):
        self.rect(x, y, 45, 20)
        if value == "unknown":
            self.glyph(x + 22, y + 10, value)
            return
        if value < 0:
            self.glyph(x + 10, y + 10, "subtract")
            x += 14
        for index in range(abs(value)):
            self.dot(x + 7 + (index % 5) * 8, y + 6 + (index // 5) * 8, 2.7)

    def bits(self, x, y, pattern, size=13):
        inset = max(1, size // 5)
        for index, bit in enumerate(pattern):
            cell = x + index * size
            self.rect(cell, y, size, size)
            if bit == "1":
                self.rect(cell + inset, y + inset, size - 2 * inset, size - 2 * inset, "black", "none")

    def value(self, x, y, value, width=4, size=11):
        self.bits(x, y, f"{value:0{width}b}", size)

    def equation(self, x, y, tokens):
        for token in tokens:
            if isinstance(token, list):
                self.quantity(x, y - 13, token[0])
                self.line(x, y + 10, x + 45, y + 10)
                self.quantity(x, y + 13, token[1])
                x += 50
            elif isinstance(token, int) or token == "unknown":
                self.quantity(x, y, token)
                x += 50
            else:
                self.glyph(x + 10, y + 10, token)
                x += 26

    def grid(self, x, y, width, height, step, fills=None):
        for row in range(height):
            for column in range(width):
                fill = fills[row][column] if fills is not None else "white"
                self.rect(x + column * step, y + row * step, step, step, fill)

    def render(self):
        return "\n".join([*self.parts, "</svg>", ""])


def stage_a(panel, data):
    panel.frame(16, 185, "A   /   Orientation, repeated structure and damage")
    for index, pattern in enumerate(data["patterns"]):
        y = 68 + index * 26
        panel.dot(65, y + 9, 4)
        panel.line(79, y + 9, 88, y + 9)
        panel.bits(97, y, pattern, 18)
        panel.line(250, y + 9, 275, y + 9)
    panel.label(296, 81, "Three matching references and one disagreement.")
    panel.label(296, 103, "The frame has a break and two unequal marks at one corner.")
    panel.label(296, 125, "A dot starts a sequence. A remote bar closes it.")
    panel.label(296, 147, "Study whether the repeated arrangement survives rotation or missing marks.")
    panel.label(296, 169, "Repetition supports an inference of structure. Cause of the disagreement is open.")


def stage_b(panel, data):
    panel.frame(217, 699, "B   /   Counting, arithmetic and relationships")
    panel.label(60, 265, "Read each repeat by comparing physical quantities.")
    panel.label(530, 265, "An empty group, then counts paired with three positions.")
    y = 288
    for tokens in data["arithmetic"]:
        fractional = isinstance(tokens[0], list)
        panel.equation(60, y + (13 if fractional else 0), tokens)
        y += 53 if fractional else 26
    for index, value in enumerate(data["counts"]):
        y = 288 + index * 25
        panel.quantity(530, y, value)
        panel.line(580, y + 10, 606, y + 10)
        panel.value(612, y + 2, value, width=3, size=16)
    for index, weight in enumerate((4, 2, 1)):
        x = 600 + index * 52
        panel.line(620 + index * 16, 485, x + 22, 506)
        panel.quantity(x, 507, weight)
    panel.label(534, 553, "Weights count four, two and one. Filled positions contribute.")
    panel.label(534, 580, "Repeated multiplication, squares and roots.")
    for index, (base, exponent, result) in enumerate(data["powers"]):
        y = 601 + index * 49
        panel.quantity(534, y + 12, base)
        panel.quantity(581, y, exponent)
        panel.glyph(640, y + 21, "eq")
        panel.quantity(658, y + 12, result)
        if exponent == 2:
            panel.glyph(734, y + 21, "root")
            panel.equation(750, y + 12, [result, "eq", base])
            panel.grid(912, y + 4, base, base, 9)
        else:
            for layer in range(base):
                panel.grid(912 + layer * 23, y + 10, base, base, 9)
    panel.label(534, 767, "Rectangular factorizations. A single row is the trivial case.")
    for index, (rows, cols) in enumerate(data["rectangles"]):
        x = 534 + index * 108
        panel.grid(x, 787, cols, rows, 10)
        panel.quantity(x, 819, rows * cols)
    panel.label(534, 869, "The diamond at left takes the value that satisfies the equation.")
    panel.label(328, 385, "Equal groups and remainders.")
    for index, (amount, group_size) in enumerate(data["factor_trials"]):
        y = 401 + index * 59
        panel.quantity(348, y, amount)
        panel.line(394, y + 10, 409, y + 10)
        rows = (amount + group_size - 1) // group_size
        panel.grid(411, y, group_size, rows, 11)
        for i in range(amount):
            panel.dot(416.5 + i % group_size * 11, y + 5.5 + i // group_size * 11, 2.6)
    panel.line(60, 891, 304, 891)
    for index, value in enumerate(range(-2, 3)):
        x = 62 + index * 49
        panel.quantity(x, 863, value)
        panel.line(x + 22, 884, x + 22, 897)
    panel.label(328, 896, "A signed line centered on the empty quantity.")


def stage_c(panel, data):
    panel.frame(932, 339, "C   /   Geometry, proportional scale and ordered motion")
    panel.dot(67, 996)
    panel.line(89, 996, 139, 996)
    panel.dot(89, 996)
    panel.dot(139, 996)
    panel.path("M178 985V1009H210M178 1001H186V1009")
    for x, scale in [(248, 1), (300, 2)]:
        panel.path(f"M{x} 1025h{24 * scale}l{-24 * scale} {-16 * scale}Z")
        panel.dot(x + 12 * scale, 1025, 2)
    for x, radius in [(402, 14), (466, 28)]:
        panel.dot(x, 1001, radius, "white")
        panel.dot(x, 1001)
        panel.line(x, 1001, x + radius, 1001)
    panel.label(60, 1059, "Point, segment, right angle, scaled triangles and circles.")
    for index, (col, row) in enumerate(data["coordinates"]):
        x = 60 + index * 115
        y = 1090
        panel.grid(x, y, 4, 4, 12)
        panel.dot(x + col * 12, y + 48 - row * 12)
        panel.dot(x, y + 48, 4, "white")
        panel.quantity(x, y + 62, col)
        panel.quantity(x + 49, y + 62, row)
    panel.label(60, 1192, "Open origin. Horizontal and vertical offsets pair with counts.")
    for index, (x, size) in enumerate([(562, 24), (670, 48)]):
        y = 1022
        panel.grid(x, y, 2 ** index, 2 ** index, size // (2 ** index))
        offset = size // 2
        panel.path(f"M{x} {y}l{offset} {-offset}h{size}v{size}l{-offset} {offset}"
                   f"m0 {-size}l{offset} {-offset}")
    for index in range(4):
        panel.grid(780 + (index % 2) * 27, 990 + (index // 2) * 27, 2, 2, 8)
    for index in range(8):
        panel.dot(857 + (index % 4) * 15, 1000 + (index // 4) * 16)
    panel.label(535, 1092, "A doubled side gives four squares and eight small cubes.")
    for index, (time, position) in enumerate(data["motion"]):
        x = 535 + index * 123
        panel.quantity(x, 1128, time)
        panel.line(x, 1175, x + 72, 1175)
        for tick in range(4):
            panel.line(x + 23 * tick, 1169, x + 23 * tick, 1181)
        panel.dot(x + 23 * position, 1175, 5)
    panel.label(535, 1214, "Equal time increments. One point changes position.")
    panel.label(60, 1249, "Orientation, projection and succession are conventions to test.")


def waveform(panel, x, y, cycles):
    path = f"M{x} {y}"
    for _ in range(cycles):
        path += " q7 -18 14 0 t14 0"
    panel.path(path)


def stage_d(panel):
    panel.frame(1287, 292, "D   /   Reference experiment: neutral hydrogen")
    for index, neutrons in enumerate((0, 1, 2)):
        x = 107 + 91 * index
        panel.dot(x, 1380, 31, "white")
        panel.dot(x, 1373, 5)
        panel.dot(x + 23, 1359, 3)
        for neutron in range(neutrons):
            panel.rect(x - 7 + neutron * 9, 1384, 6, 6)
    panel.path("M80 1417v8h55v-8")
    panel.label(62, 1455, "One proton, one electron, no neutrons.")
    panel.label(62, 1477, "Compare hydrogen isotopes. Rings are schematic.")
    panel.line(417, 1368, 536, 1368)
    panel.line(417, 1446, 536, 1446)
    for index in range(3):
        panel.dot(441 + index * 34, 1365, 4)
    panel.dot(475, 1443, 4)
    panel.path("M495 1376V1433L489 1425M495 1433L501 1425")
    waveform(panel, 554, 1406, 3)
    panel.label(407, 1480, "Ground-state levels at zero magnetic field.")
    panel.label(407, 1502, "One photon carries away the energy difference.")
    panel.label(407, 1524, "Three upper spin projections and one lower.")
    for index, cycles in enumerate((2, 3)):
        y = 1376 + index * 68
        waveform(panel, 780, y, cycles)
        panel.path(f"M780 {y + 14}v6h{28 * cycles}v-6")
        panel.quantity(780 + 28 * cycles + 9, y - 9, cycles)
    panel.label(749, 1495, "Count wavelengths along space.")
    panel.label(749, 1517, "At one point, count cycles in time.")
    panel.label(62, 1550, "Candidate reference. The spectrum, level diagrams and measurement conditions require further testing.")


def raster_rows(panel, record, x, y, show_output=True):
    rows = record["rows"]
    width, height = len(rows[0]), len(rows)
    mode = record["mode"]
    fields = (record["id"], mode, width, height, width * height)
    panel.dot(x + 2, y + 5, 4)
    for index, field in enumerate(fields):
        panel.value(x + 13 + index * 48, y, field, size=9)
    panel.line(x + 255, y - 3, x + 255, y + 13)
    panel.line(x + 259, y - 3, x + 259, y + 13)
    for row, samples in enumerate(rows):
        cursor = x + 12
        for sample in samples:
            components = sample if mode == 2 else [sample]
            for component in components:
                digits = 1 if mode == 0 else 3
                panel.value(cursor, y + 22 + row * 14, component, width=digits, size=8)
                cursor += digits * 8 + (2 if mode == 2 else 4)
            if mode == 2:
                cursor += 8
        panel.line(cursor + 3, y + 20 + row * 14, cursor + 3, y + 31 + row * 14)
    panel.line(x + 3, y + 25 + height * 14, x + 32, y + 25 + height * 14, 2)
    if show_output:
        max_code = 1 if mode == 0 else 7
        fills = []
        for samples in rows:
            channels = [sample if mode == 2 else [sample] * 3 for sample in samples]
            fills.append([
                "#" + "".join(f"{round(value * 255 / max_code):02x}" for value in rgb)
                for rgb in channels
            ])
        panel.grid(x + 297, y + 20, width, height, 19, fills)
        for row in range(height):
            panel.dot(x + 289, y + 29 + 19 * row, 2)
        for column in range(width):
            panel.dot(x + 306 + 19 * column, y + 12, 2)


def stage_e(panel, data):
    panel.frame(1595, 535, "E   /   Toy frames, pixel position, intensity and channels")
    panel.label(60, 1641, "Start dot, then five four-position fields.")
    panel.label(60, 1662, "Fields are record ID, mode, width, height and sample count.")
    panel.label(540, 1641, "Read across rows. Compare the paired raster.")
    panel.label(540, 1662, "Modes encode two states, intensity or three channels.")
    for index, record in enumerate(data["rasters"]):
        raster_rows(panel, record, 60 + (index % 2) * 480, 1690 + (index // 2) * 94)
    for level in range(8):
        x = 60 + level * 36
        panel.value(x, 1890, level, width=3, size=8)
        value = round(level * 255 / 7)
        panel.rect(x, 1904, 24, 24, f"#{value:02x}{value:02x}{value:02x}")
    for index, color in enumerate(("#ff0000", "#00ff00", "#0000ff")):
        x = 540 + index * 68
        for channel in range(3):
            panel.value(x + channel * 21, 1890, 7 if channel == index else 0, width=3, size=6)
        panel.rect(x, 1904, 60, 24, color)
    panel.label(370, 1921, "Intensity ramp")
    panel.label(750, 1921, "Channel reference swatches")
    for index, value in enumerate((1, 2, 4, 8)):
        x = 60 + index * 143
        panel.value(x, 1950, value, width=8, size=11)
        panel.quantity(x + 90, 1946, value)
    panel.label(655, 1961, "Eight positions encode larger counts.")
    for index, (lower, upper) in enumerate(((-14, 19), (-27, 10))):
        x = 60 + index * 480
        center = 2043
        panel.path(f"M{x + 100} {center - 39}v34m0 10v34")
        panel.path(f"M{x + 200} {center - 32}v64")
        panel.line(x + 178, center, x + 222, center, 1)
        for offset in (lower, upper):
            panel.dot(x, center + offset, 4)
            panel.line(x, center + offset, x + 200, center - offset)
            panel.dot(x + 200, center - offset, 3)
        panel.label(x, 2104, "Two points project through an opening to a sampling plane.")


def render_ladder(data, annotated=False):
    panel = Panel(2146, annotated)
    stage_a(panel, data)
    stage_b(panel, data)
    stage_c(panel, data)
    stage_d(panel)
    stage_e(panel, data)
    return panel.render()


def render_trial(data):
    trial = data["trial"]
    panel = Panel(569)
    panel.frame(16, 84, "")
    panel.bits(60, 56, trial["orientation"], 18)
    panel.frame(114, 92, "")
    panel.value(60, 152, trial["number"], width=4, size=15)
    panel.equation(225, 151, trial["arithmetic"])
    panel.frame(220, 99, "")
    panel.grid(60, 246, 4, 4, 14)
    panel.dot(60, 302, 4, "white")
    for index, value in enumerate(trial["coordinate"]):
        panel.quantity(145 + 50 * index, 268, value)
    panel.frame(333, 220, "")
    for index, record in enumerate(trial["rasters"]):
        raster_rows(panel, record, 60 + 480 * (index % 2), 370 + 96 * (index // 2), show_output=False)
    return panel.render()


def outputs(data):
    return {
        "primer-ladder.svg": render_ladder(data),
        "primer-ladder-annotated.svg": render_ladder(data, annotated=True),
        "primer-ladder-trial.svg": render_trial(data),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DOCS)
    parser.add_argument("--check", action="store_true", help="check committed diagrams for drift")
    args = parser.parse_args()
    data = json.loads((DOCS / "primer-ladder-data.json").read_text(encoding="utf-8"))
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs(data).items():
        path = args.output_dir / name
        if args.check:
            if not path.is_file() or path.read_bytes() != content.encode("utf-8"):
                parser.error(f"stale or missing diagram: {path}")
        else:
            path.write_bytes(content.encode("utf-8"))


if __name__ == "__main__":
    main()
