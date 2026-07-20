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
    { res: 5, minzoom: 7, maxzoom: 8 },
];

export function bandForZoom(zoom: number): HexBand {
    const z = Math.floor(Math.max(0, Math.min(8, zoom)));
    return HEX_BANDS.find((band) => z >= band.minzoom && z <= band.maxzoom) ?? HEX_BANDS[0]!;
}
