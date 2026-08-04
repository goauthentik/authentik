# @goauthentik/geo

Generator for the hexworld basemap archive that authentik's events map renders.

This package is build-time machinery only — nothing here ships to the browser.
It turns Natural Earth vector data and a Protomaps planet dump into
`tiles/hexworld.pmtiles`, the archive `web` copies into its bundle. The map
element itself, and the styles that read this archive, live in
`web/src/elements/maps/`.

## The contract with the runtime

Three things must agree between the archive and the element that draws it, so
the element owns them and this package imports them rather than redeclaring:

| What                         | Owned by                               |
| ---------------------------- | -------------------------------------- |
| Zoom → H3 resolution bands   | `web/src/elements/maps/bands.ts`       |
| Label kinds and reveal zooms | `web/src/elements/maps/labels.ts`      |
| Attribution string           | `web/src/elements/maps/attribution.ts` |

All three are import-free for this reason — pulling them from the style module
would drag MapLibre into a Node build script. The dependency runs one way only:
tooling reads the app's contract, never the reverse.

## Tests

```bash
pnpm run test         # Vitest, node only
pnpm run lint:types   # tsc over src, scripts and test
```

Covers the land-fill, border, country-assignment, detail-zone and label
normalization math. The element's own tests live with the element, under
`web/test/unit/maps/` and `web/test/component/`.

## Zoom bands

The hexworld archive baked at build time uses three H3 resolutions (`HEX_BANDS`
in `src/hexworld/bands.ts`). Measured via h3's `getHexagonEdgeLengthAvg` and
`getHexagonAreaAvg` — cell "width" here means vertex-to-opposite-vertex,
roughly 2× the edge:

| Zoom range | H3 resolution | Edge length | Cell width | Cell area   |
| ---------- | ------------- | ----------- | ---------- | ----------- |
| z0–z2      | 3             | ~69 km      | ~138 km    | ~12,393 km² |
| z3–z6      | 4             | ~26 km      | ~52 km     | ~1,770 km²  |
| z7         | 5             | ~10 km      | ~20 km     | ~253 km²    |

z7 is the archive's `maxzoom`; MapLibre overzooms beyond it, and `bandForZoom`
clamps to the res-5 band so events keep binning at that resolution. The bands
are baked into every published archive — changing `HEX_BANDS` invalidates
existing tiles.

## The shipped archive

`tiles/hexworld.pmtiles` is committed to the repo. The current file is the
`detail` cut (~22 MiB): a full res-3/res-4 grid worldwide, plus a res-5 overlay
restricted to the populated-area detail zone (see `src/hexworld/detail-zone.ts`).

`tiles/fonts/` ships the Latin Noto Sans glyph ranges (Regular + Medium, 0-255
and 256-511) alongside the archive, under SIL Open Font License 1.1 (see
`tiles/fonts/OFL.txt`). Both the archive and the glyphs are committed so the
web build stays hermetic — no network required after clone.

The `web` build copies `tiles/hexworld.pmtiles` and `tiles/fonts/` into
`web/dist/assets/maps/`. If either is missing at build time the build fails
loudly instead of silently shipping a broken map.

## Regenerating the archive

The generator lives at `scripts/build-hexworld.ts`. It needs:

- Node ≥ 24 and this workspace installed (`pnpm install`).
- [tippecanoe](https://github.com/felt/tippecanoe) and [go-pmtiles](https://github.com/protomaps/go-pmtiles) on `PATH`.
- A local PMTiles planet dump extracted to z0–8 (a ~1–3 GB slice of a Protomaps planet build).

```bash
# Preview the shell pipeline without running it:
pnpm run hexworld:build -- --dry-run --out tiles

# Full run — emits both size cuts:
pnpm run hexworld:build -- --dump ./planet-z8.pmtiles --out tiles
# tiles/hexworld-detail.pmtiles  ← res 3 + 4 + zoned res 5  (shipped)
# tiles/hexworld-plain.pmtiles   ← res 3 + 4 only  (smaller, coarser)
```

Inputs the generator downloads on first run are pinned to specific releases so a re-run a year from now produces the same tiles:

- Natural Earth vector data: `nvkelso/natural-earth-vector@v5.1.2`. `ne_50m_land.geojson` supplies the land polygons and `ne_50m_admin_0_countries.geojson` the country assignment; state and province borders come from `ne_10m_admin_1_states_provinces.geojson` since the 50m admin-1 dataset only covers nine countries.
- Protomaps planet build: `20260521` — the source of the labels layer. The shipped archive was cut from that build; regenerate against a newer build to pick up new places.

The generator walks land, country, and region data into H3 cells, extracts labels from the dump's `places` layer via pmtiles + MVT decoders, computes border segments along shared cell edges wherever two adjacent cells differ (country borders take precedence over region borders at the same edge), then hands everything to tippecanoe and tile-join. Border features carry a `level` property so the runtime style can render country and region borders with different weights from the same source-layer. Cuts are always emitted together; size is a manual gate — pick whichever fits the ship budget after inspecting both in the pmtiles viewer.

To ship a regenerated archive, copy the chosen cut over the committed one:

```bash
AUTHENTIK_HEXWORLD_SOURCE=/path/to/hexworld-detail.pmtiles \
  pnpm run tiles:pull-hexworld
git add tiles/hexworld.pmtiles && git commit
```

## Runtime override

A brand can point the events map at its own tile server (**System > Brands >
Map tiles**), which bypasses this archive entirely — see
`web/src/elements/maps/basemap-style.ts`.
