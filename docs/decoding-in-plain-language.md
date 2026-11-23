# How decoding works: a concrete example

We want to communicate something to a reader who knows **nothing** about our language, our operating systems or our file formats. It is tempting to place a ZIP or memory chip on a spacecraft and hope a reader can open it. This only stores bits; it does not explain what they represent.

## Recovering information is different from understanding it

Imagine 64 physical marks that can each have two distinguishable appearances. Humans might write those as 0 and 1. That notation is not universal. A reader must establish:

1. The plate has intentionally arranged marks, and which way it should be oriented.
2. There are two different kinds of marks, and their order matters.
3. There are exactly 64 ordered values in this example.
4. The values should be arranged into eight columns and eight rows.
5. Where to start, which direction to move, and whether each value means light or dark.
6. How those cells together correspond to a picture.

Now consider a saved sequence of 64 values. **Row-first** means put the first eight across the top row, the next eight across the second row, and so on. **Column-first** means put the first eight down the left column. Both produce an 8-by-8 grid, but one may yield a very different picture. Neither arrangement is deducible just from the 64 bits.

The interactive experiment in `website/guide.html` illustrates this exact ambiguity. It does **not** teach an unfamiliar species to recognize a picture, much less to understand English. A physical primer must use examples where a directly visible grid is paired with its representation as distinct marks, preferably in more than one orientation and with independently identifiable geometry.

## Why chemistry and physics enter the primer

Numbers and equations alone are not enough if we haven't defined their units. A reproducible atomic spectral transition could serve as a proposed reference, but the selection and exact physical demonstration remain open engineering work. A length marker expressed in familiar Earth units without explanation would be no better than an unexplained word.

## Then what about actual sound?

A simple waveform can be specified as an ordered sequence of measured values at known time intervals. To reconstruct it, a reader must infer sample count, sampling interval, amplitude scale, sign convention and output interpretation. Voices and music come much later, after the basic mapping has been demonstrated.

## What the current prototype does and doesn't accomplish

Today Python reads a file of literal ASCII symbols and turns them into pixels. This demonstrates software conversion **for a human who already knows the conventions**. It is not yet an independently reconstructed physical record.

Our next meaningful test is to manufacture or print a prototype with pictorial clues, hide all instructions, and ask multiple unfamiliar human volunteers to reconstruct a tiny image. Record every incorrect guess, then revise. Independent tests are not proof of alien comprehension but can expose human conventions the designer overlooked.

This is the central research question of Centauri Archive: can a future reader derive enough common structure from the artifact itself to interpret meaningful information?
