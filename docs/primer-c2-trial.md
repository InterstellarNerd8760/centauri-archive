# Facilitator protocol for C2 readout

This document is for facilitators and scorers. Use the [C2 text-free training panel](primer-c2.svg) and a separately printed or locally displayed [held-out sheet](primer-c2-trial.svg). Supply only rendered versions, with filenames and metadata hidden. The source JSON, examples with English labels, convention catalog, source repository and facilitator documents stay out of the trial environment. Use an offline viewing session or a paper packet with no answer material. For a screen trial, use an isolated viewer with only the training and task images loaded. Zoom and pan may be used for the conditions that permit enlargement. Rendering the SVG to a high-resolution, fixed raster for a screen trial avoids exposing SVG objects or embedded labels.

## Steps

1. Pre-register eligibility, stimuli, exact transformations, allowed tools, stopping time and scoring. Test whether the print or display faithfully shows the fine marks at an allowed magnification. Record distance or display scale, pixel dimensions, viewing tools, lighting and actual printed feature widths if relevant.
2. Give the participant the unlabeled C1 and C2 training diagrams. Keep standard instructions neutral, such as “What relationships do you see? Show what pieces of the next sheet belong together and write down what you can recover.”
3. Supply the held-out sheet without an enlarged inset. Leave the training reference in reach. Ask the participant to identify a target, indicate its starting point and scan directions, and record all observable open and filled states plus unknown positions. Record the first answer and alternative interpretations before any prompting.
4. Compare a baseline to independent sessions with a rotated or mirrored sheet, a small intentional occlusion, and permitted or unavailable enlargement. Use a purpose-built known-damage overlay with a separately recorded mask. Clearly distinguish simulation on paper or a display from evidence on a fabricated coupon.
5. Have a scorer record the chosen target, tag inference, orientation, hypothesized pitch ratio, scan order, the exact array, time and reasons for ambiguity. If tools or hints were supplied after the first answer, retain the assisted result separately.

## Scoring and evaluator key

Stage F uses the same two-state markings as C1. Score target matching, orientation, pitch inference and row transcription separately. For each field, mark exact, partial, incompatible or missing. Calculate observed cell agreement over readable cells and report the count of unknown positions separately. An exact baseline recovery must have three correctly oriented rows, 24 correct cell states and zero unknowns.

The requested region is the upper-right tile. Its tag is `0110` (six). At the recorded orientation the large fiducial mark precedes the small mark along the row axis. The intended enlargement is fourfold. The three held-out rows are `10111000`, `00101110`, and `11000001`, in that order. For alternate views, undo the applied transformation before comparing to the key. Comparison is on the inset state. No display-color assumptions enter into the score.

Retain small sample uncertainty, non-completions and discordant cases in the report. Results apply to the recruited human population, supplied tools and tested specimen. No trial results have been collected.
