# Static hosting after review

Build locally with `python3 tools/build_site.py` and serve `build/site` with any static server. The build regenerates and verifies the downloadable package, copies its manifest byte for byte, and publishes the text samples beside the catalogue. Archive records and original diagrams are served locally. The current site also requests optional Google Fonts, with system fallbacks; the archive itself does not depend on fonts.

The repository now also contains a GitHub Pages workflow on the main branch. For an alternative Cloudflare Pages deployment, configure the following values after approval.

| Setting | Value |
| --- | --- |
| Production branch | main |
| Framework preset | None |
| Root directory | Repository root |
| Build command | python3 tools/build_site.py |
| Output directory | build/site |
| Runtime | Python 3.10 or later; standard library only |

For a future subdomain such as archive.<your-domain>, add the chosen hostname under the Pages project's Custom domains. For external DNS, create a CNAME at that label pointing to the assigned project.pages.dev hostname. For a Cloudflare-managed zone, follow the dashboard's record setup. Check certificate activation and the ZIP download over HTTPS once approved. The repository has a Pages deployment workflow; it does not contain DNS credentials.

References: [Cloudflare build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/) and [custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/).
