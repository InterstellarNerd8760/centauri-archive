# Centauri Archive

Centauri Archive is an independent experiment in making a compact record of Earth, life and human civilization readable long after its original software disappears. The Fermi Explorer interstellar mission inspired the project. The intended next step is a proposed payload contribution. Mission affiliation, payload acceptance, hardware selection and flight qualification have not been established.

## Try the prototype

From the repository root with Python 3.10 or newer:

```sh
python3 tools/archive.py build build/centauri.zip
python3 tools/archive.py inspect build/centauri.zip
python3 tools/archive.py verify build/centauri.zip
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
python3 -m http.server 8000 --directory build/site
```

Open http://localhost:8000 for the website. An ordinary ZIP reader can open the package. Start with `content/primer/start.txt` and compare the files against `manifest.json`. No network, package installation or proprietary reader is required.

## Design objectives

- Fit a meaningful prototype into 1–10 MB (decimal, including the container).
- Make byte order, raster dimensions, units and file boundaries explicit.
- Reproduce the same package bytes from the same source bytes. Detect accidental changes to contents using SHA-256.
- Give a reader a path from visible marks to bits, from bits to pictures and from pictures to human descriptions. The physical stage is a design proposal.

| Directory | Purpose |
| --- | --- |
| [archive](archive/) | Original records and the in-package reading guide |
| [tools](tools/) | Deterministic package builder, inspector, verifier and website assembly |
| [docs](docs/) | [Package specification](docs/format.md), [engineering notes](docs/engineering.md) and [hosting guide](docs/hosting.md) |
| [tests](tests/) | Automated package and website checks |
| [website](website/) | Static public interface and original illustration |

The first collection pairs short original texts with a deterministic grayscale test plate. The plate gives readers a known image against which to check their decoding. Current validation covers digital behavior. Survival, manufacturability and interpretation by unfamiliar readers remain open research questions.
