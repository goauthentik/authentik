/**
 * @file Attribution for the bundled hexworld basemap.
 *
 * Kept free of imports: the archive generator in `packages/geo` stamps this
 * same string into the PMTiles metadata, and pulling it from the style module
 * would drag MapLibre and the Protomaps basemap into a Node build script.
 *
 * Plain text by design — the airgap test forbids external URLs in the style,
 * and an in-app link target makes no sense here. The docs page carries the
 * osm.org/copyright link; ODbL text attribution suffices on the map itself.
 */
export const HEXWORLD_ATTRIBUTION = "© OpenStreetMap (labels) · Natural Earth";
