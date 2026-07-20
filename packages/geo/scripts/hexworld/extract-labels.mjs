import { NodeFileSource } from "./node-file-source.mjs";

import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";
import { PMTiles } from "pmtiles";

import { dedupePlaces, normalizePlace } from "../../out/hexworld/labels.js";

const MAX_ZOOM = 8;

function decodeTile(tile, x, y, z, places) {
    const layer = new VectorTile(new Pbf(tile.data)).layers.places;
    if (!layer) return;
    for (let i = 0; i < layer.length; i++) {
        const feature = layer.feature(i).toGeoJSON(x, y, z);
        if (feature.geometry.type !== "Point") continue;
        const [lng, lat] = feature.geometry.coordinates;
        const place = normalizePlace(feature.properties, lng, lat);
        if (place) places.push(place);
    }
}

/** Decode every places-layer feature in z0..z8 of a local pmtiles archive. */
export async function extractLabels(dumpPath, { onProgress } = {}) {
    const source = new NodeFileSource(dumpPath);
    const archive = new PMTiles(source);
    const places = [];
    let decoded = 0;

    for (let z = 0; z <= MAX_ZOOM; z++) {
        const side = 2 ** z;
        for (let x = 0; x < side; x++) {
            for (let y = 0; y < side; y++) {
                const tile = await archive.getZxy(z, x, y);
                if (!tile?.data) continue;
                decodeTile(tile, x, y, z, places);
                decoded += 1;
                if (decoded % 5000 === 0) onProgress?.(decoded, places.length);
            }
        }
    }

    await source.close();
    return dedupePlaces(places);
}
