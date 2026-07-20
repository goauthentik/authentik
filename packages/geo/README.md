# @goauthentik/geo

Map component and basemap tooling for authentik's events overview.

The package ships a Lit `<ak-map>` element wrapping [MapLibre GL](https://maplibre.org/) and two style builders that back it:

- `buildBasemapStyle(options)` — conventional [Protomaps](https://protomaps.com/) vector basemap loaded from a `pmtiles://` archive or an XYZ template. Used when a brand configures a tile URL under **System > Brands > Map tiles**.
- `buildHexworldStyle(options)` — the zero-config default. Renders land as an H3 hexagonal grid with country borders drawn along hex edges plus country / region / locality labels, from a small bundled PMTiles archive. Enters when `pmtiles-url` on `<ak-map>` is empty.

`<ak-map>` also aggregates its `markers` prop into cells and paints them via MapLibre feature-state, so event counts light up hexes without any per-marker DOM overhead.

## Zoom bands

The hexworld archive baked at build time uses three H3 resolutions:

| Zoom range | H3 resolution | Rough cell width |
| ---------- | ------------- | ---------------- |
| z0–z3      | 3             | ~1000 km         |
| z4–z6      | 4             | ~400 km          |
| z7–z8      | 5             | ~130 km          |

MapLibre overzooms past z8. The bands are baked into every published archive — changing `HEX_BANDS` invalidates existing tiles.

## The shipped archive

`tiles/hexworld.pmtiles` is committed to the repo. The current file is the
res 3 + 4 cut (`hexworld-r4`, ~8.8 MB) — smaller than the res-5 cut and still
sharper than GeoIP-derived event locations warrant.

`tiles/fonts/` ships the Latin Noto Sans glyph ranges (Regular + Medium, 0-255
and 256-511) alongside the archive, under SIL Open Font License 1.1 (see
`tiles/fonts/OFL.txt`). Both the archive and the glyphs are committed so the
web build stays hermetic — no network required after clone.

The `web` build copies `tiles/hexworld.pmtiles` and `tiles/fonts/` into
`web/dist/assets/maps/`. If either is missing at build time the build fails
loudly instead of silently shipping a broken map.

## Regenerating the archive

The generator lives at `scripts/hexworld/build.mjs`. It needs:

- Node ≥ 24 and this workspace installed (`pnpm install`).
- [tippecanoe](https://github.com/felt/tippecanoe) and [go-pmtiles](https://github.com/protomaps/go-pmtiles) on `PATH`.
- A local PMTiles planet dump extracted to z0–8 (a ~1–3 GB slice of a Protomaps planet build).

```bash
# Preview the shell pipeline without running it:
node scripts/hexworld/build.mjs --dry-run --out tiles

# Full run — emits both size cuts:
node scripts/hexworld/build.mjs --dump ./planet-z8.pmtiles --out tiles
# tiles/hexworld-r4.pmtiles  ← res 3 + 4  (smaller, coarser detail)
# tiles/hexworld-r5.pmtiles  ← res 3 + 4 + 5  (larger, finer detail)
```

Inputs the generator downloads on first run are pinned to specific releases so a re-run a year from now produces the same tiles:

- Natural Earth vector data: `nvkelso/natural-earth-vector@v5.1.2` (`ne_50m_land.geojson` for the land polygons, `ne_50m_admin_0_countries.geojson` for country assignment and hex-aligned borders).
- Protomaps planet build: `20260521` — the source of the labels layer. The shipped archive was cut from that build; regenerate against a newer build to pick up new places.

The generator walks land + country data into H3 cells, extracts labels from the dump's `places` layer via pmtiles + MVT decoders, computes border segments along shared cell edges wherever two adjacent cells belong to different countries, then hands everything to tippecanoe and tile-join. Cuts are always emitted together; size is a manual gate — pick whichever fits the ship budget after inspecting both in the pmtiles viewer.

To ship a regenerated archive, copy the chosen cut over the committed one:

```bash
AUTHENTIK_HEXWORLD_SOURCE=/path/to/hexworld-r4.pmtiles \
  pnpm run tiles:pull-hexworld
git add tiles/hexworld.pmtiles && git commit
```

## Runtime override

Non-empty `pmtiles-url` on `<ak-map>` (usually set via the brand config) selects `buildBasemapStyle` and skips hexworld entirely; the two paths do not interact.
