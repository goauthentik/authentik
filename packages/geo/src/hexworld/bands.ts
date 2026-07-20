export interface HexBand {
    res: number;
    minzoom: number;
    maxzoom: number;
}

/**
 * Canonical zoom→H3-resolution mapping, shared by the generator and the runtime overlay.
 * Changing a band invalidates published archives.
 */
export const HEX_BANDS: readonly HexBand[] = [
    { res: 3, minzoom: 0, maxzoom: 2 },
    { res: 4, minzoom: 3, maxzoom: 6 },
    { res: 5, minzoom: 7, maxzoom: 7 },
];

/** Highest zoom the archive carries geometry for; MapLibre overzooms beyond it. */
export const MAX_BAND_ZOOM = HEX_BANDS[HEX_BANDS.length - 1]!.maxzoom;

export function bandForZoom(zoom: number): HexBand {
    // Clamp to the last band rather than a literal: past MAX_BAND_ZOOM the map
    // is showing overzoomed tiles from that band, so events must resolve to its
    // resolution, not fall through to the coarsest one.
    const z = Math.floor(Math.max(0, Math.min(MAX_BAND_ZOOM, zoom)));
    return HEX_BANDS.find((band) => z >= band.minzoom && z <= band.maxzoom) ?? HEX_BANDS[0]!;
}
