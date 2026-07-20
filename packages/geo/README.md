# @goauthentik/geo

Map component and basemap tooling for authentik's events overview.

The package ships a Lit `<ak-map>` element wrapping [MapLibre GL](https://maplibre.org/) and two style builders that back it:

- `buildBasemapStyle(options)` — conventional [Protomaps](https://protomaps.com/) vector basemap loaded from a `pmtiles://` archive or an XYZ template. Used when a brand configures a tile URL under **System > Brands > Map tiles**.
- `buildHexworldStyle(options)` — the zero-config default. Renders land as an H3 hexagonal grid with country / region / locality labels, from a small bundled PMTiles archive. Enters when `pmtiles-url` on `<ak-map>` is empty.

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

The `web` build copies the archive into `web/dist/assets/maps/hexworld.pmtiles`.
Glyphs (Noto Sans Latin ranges) are fetched from the Protomaps CDN on the
first build and cached under `tiles/fonts/`; subsequent builds reuse the
cache. Override the CDN via `AUTHENTIK_HEXWORLD_GLYPHS` for airgapped
environments.

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

The generator downloads Natural Earth 50m land once, walks every tile of the dump's `places` layer through pmtiles + MVT decoders, and hands the results off to tippecanoe and tile-join. The cuts are always emitted together; the size decision is a manual gate — pick whichever fits the ship budget after inspecting both in the pmtiles viewer.

To ship a regenerated archive, copy the chosen cut over the committed one:

```bash
AUTHENTIK_HEXWORLD_SOURCE=/path/to/hexworld-r4.pmtiles \
  pnpm run tiles:pull-hexworld
git add tiles/hexworld.pmtiles && git commit
```

## Runtime override

Non-empty `pmtiles-url` on `<ak-map>` (usually set via the brand config) selects `buildBasemapStyle` and skips hexworld entirely; the two paths do not interact.
