import { type FileHandle, open } from "node:fs/promises";

import { dedupePlaces, normalizePlace, type PlaceLabel } from "@goauthentik/geo/shared";

import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";
import { PMTiles, type RangeResponse } from "pmtiles";

const MAX_ZOOM = 8;

/** Pmtiles Source backed by a local file handle. */
export class NodeFileSource {
    #path: string;
    #handle: FileHandle | undefined;

    constructor(path: string) {
        this.#path = path;
    }

    public getKey() {
        return this.#path;
    }

    async getBytes(offset: number, length: number): Promise<{ data: ArrayBuffer }> {
        this.#handle ??= await open(this.#path, "r");
        const buffer = Buffer.alloc(length);
        await this.#handle.read(buffer, 0, length, offset);
        return { data: buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + length) };
    }

    public async close() {
        await this.#handle?.close();
    }
}

function decodeTile(tile: RangeResponse, x: number, y: number, z: number, places: PlaceLabel[]) {
    const layer = new VectorTile(new Pbf(tile.data)).layers.places;

    if (!layer) return;

    for (let i = 0; i < layer.length; i++) {
        const feature = layer.feature(i).toGeoJSON(x, y, z);

        if (feature.geometry.type !== "Point") continue;
        if (!feature.properties) continue;

        const [lng, lat] = feature.geometry.coordinates;

        const place = normalizePlace(feature.properties, lng!, lat!);

        if (place) {
            places.push(place);
        }
    }
}

export type ExtractLabelsProgress = (decodedTiles: number, decodedPlaces: number) => void;

export interface ExtractLabelsOptions {
    onProgress?: ExtractLabelsProgress;
}

/** Decode every places-layer feature in z0..z8 of a local pmtiles archive. */
export async function extractLabels(dumpPath: string, { onProgress }: ExtractLabelsOptions = {}) {
    const source = new NodeFileSource(dumpPath);
    const archive = new PMTiles(source);
    const places: PlaceLabel[] = [];
    let decoded = 0;

    for (let z = 0; z <= MAX_ZOOM; z++) {
        const side = 2 ** z;

        for (let x = 0; x < side; x++) {
            for (let y = 0; y < side; y++) {
                const tile = await archive.getZxy(z, x, y);

                if (!tile?.data) continue;

                decodeTile(tile, x, y, z, places);

                decoded += 1;

                if (decoded % 5000 === 0) {
                    onProgress?.(decoded, places.length);
                }
            }
        }
    }

    await source.close();

    return dedupePlaces(places);
}
