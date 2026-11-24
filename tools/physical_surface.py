"""Lay protected slots onto a parametric, illustrative sampled surface."""
import argparse
from dataclasses import dataclass
import json

from physical_recovery import encode_specimen, recover_specimen
from research_archive import frame, sample_records


@dataclass(frozen=True)
class Surface:
    width_um: int
    height_um: int
    pitch_um: int
    planes: int = 1
    primer_rows: int = 4

    def __post_init__(self):
        integers = (self.width_um, self.height_um, self.pitch_um, self.planes, self.primer_rows)
        if any(type(value) is not int for value in integers) or min(integers[:4]) <= 0:
            raise ValueError("surface dimensions, pitch and planes must be positive integers")
        if not 0 <= self.primer_rows < self.rows or not self.columns or self.usable_bits > 16_777_216:
            raise ValueError("invalid or oversized illustration grid")

    @property
    def columns(self):
        return self.width_um // self.pitch_um

    @property
    def rows(self):
        return self.height_um // self.pitch_um

    @property
    def data_rows(self):
        return self.rows - self.primer_rows

    @property
    def usable_bits(self):
        return self.columns * self.data_rows * self.planes

    def sample(self, data, obscured=()):
        """Treat each obscured rectangle's sampled cells as zeros rather than known erasures."""
        if len(data) * 8 > self.usable_bits:
            raise ValueError("protected specimen does not fit in the modeled grid")
        sampled = bytearray(data)
        plane_bits = self.columns * self.data_rows
        affected = 0
        for plane, left, top, width, height in obscured:
            if (not 0 <= plane < self.planes or min(left, top, width, height) < 0
                    or left + width > self.columns or top + height > self.rows):
                raise ValueError("obscured region falls outside the modeled surface")
            for row in range(max(top, self.primer_rows), top + height):
                start = plane * plane_bits + (row - self.primer_rows) * self.columns + left
                for i in range(start, min(start + width, len(sampled) * 8)):
                    mask = 128 >> (i % 8)
                    affected += bool(sampled[i // 8] & mask)
                    sampled[i // 8] &= 255 ^ mask
        return bytes(sampled), affected


def measure(surface):
    records = {record.id: frame(record) for record in sample_records()}
    data = encode_specimen(records)
    clean_data, _ = surface.sample(data)
    # A transverse scratch through the data rectangle, far from the reserved
    # primer band. Its position scales with the sampled stream, not a material.
    middle_bit = len(data) * 4
    plane, local_bit = divmod(middle_bit, surface.columns * surface.data_rows)
    row = surface.primer_rows + local_bit // surface.columns
    damaged, changed = surface.sample(data, [(plane, 0, row, surface.columns, 1)])
    before, after, combined = (recover_specimen(copies) for copies in
                               ([clean_data], [damaged], [damaged, clean_data]))
    return {
        "width_um": surface.width_um, "height_um": surface.height_um,
        "pitch_um": surface.pitch_um, "planes": surface.planes, "primer_rows": surface.primer_rows,
        "columns": surface.columns, "rows": surface.rows, "usable_bits": surface.usable_bits,
        "stored_bytes": len(data), "obscured_region": {"plane": plane, "row": row, "width_cells": surface.columns},
        "changed_sample_bits": changed, "records_before": len(before.records),
        "records_after": len(after.records), "missing_after": list(after.missing_ids),
        "combined_records": len(combined.records),
        "incorrect_accepted": sum(data != records.get(number) for stage in (before, after, combined)
                                  for number, data in stage.records.items()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width-um", type=int, default=40_000)
    parser.add_argument("--height-um", type=int, default=40_000)
    parser.add_argument("--pitch-um", type=int, default=80)
    parser.add_argument("--planes", type=int, default=1)
    parser.add_argument("--primer-rows", type=int, default=4)
    args = parser.parse_args()
    try:
        print(json.dumps(measure(Surface(args.width_um, args.height_um, args.pitch_um,
                                         args.planes, args.primer_rows)), indent=2))
    except ValueError as error:
        parser.exit(1, f"surface study: {error}\n")


if __name__ == "__main__":
    main()
