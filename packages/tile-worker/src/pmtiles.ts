import { decompressPMTileBuffer } from "./compression.js";
import { TileTypeContentType, TileTypeFileExtensionMap } from "./files.js";
import { R2Source, type R2SourceConfig } from "./r2-source.js";

import { PMTiles, type RangeResponse, ResolvedValueCache, type TileType } from "pmtiles";

export interface ReadTileParams {
    tileType: TileType;
    z: number;
    x: number;
    y: number;
}

export interface TileRangeResult extends RangeResponse {
    contentType: string;
}

export interface TileJSON {
    tilejson: "3.0.0";
    name?: string;
    description?: string;
    attribution?: string;
    scheme: "xyz";
    tiles: string[];
    version?: string;
    bounds: [number, number, number, number];
    center: [number, number, number];
    minzoom: number;
    maxzoom: number;
    vector_layers?: unknown[];
}

const sharedCache = new ResolvedValueCache(25, false, decompressPMTileBuffer);

export class CloudflareWorkerPMTiles extends PMTiles {
    static from(config: R2SourceConfig): CloudflareWorkerPMTiles {
        const source = new R2Source(config);
        return new CloudflareWorkerPMTiles(source, sharedCache, decompressPMTileBuffer);
    }

    async retrieveTile(params: ReadTileParams): Promise<TileRangeResult | null> {
        const header = await this.getHeader();

        if (header.tileType !== params.tileType) {
            const error = new Error(
                `Tile type mismatch: requested ${params.tileType}, archive is ${header.tileType}`,
            );
            (error as Error & { status?: number }).status = 400;
            throw error;
        }

        if (params.z < header.minZoom || params.z > header.maxZoom) {
            const error = new Error(
                `Zoom ${params.z} outside archive range [${header.minZoom}, ${header.maxZoom}]`,
            );
            (error as Error & { status?: number }).status = 404;
            throw error;
        }

        const range = await this.getZxy(params.z, params.x, params.y);
        if (!range) return null;

        return {
            ...range,
            contentType: TileTypeContentType[header.tileType],
        };
    }

    async retrieveTileJSON(tileSetName: string, publicUrl: string): Promise<TileJSON> {
        const [header, rawMetadata] = await Promise.all([this.getHeader(), this.getMetadata()]);
        const fileExtension = TileTypeFileExtensionMap.get(header.tileType) ?? "mvt";
        const meta = (rawMetadata ?? {}) as Partial<TileJSON> & { vector_layers?: unknown[] };

        return {
            tilejson: "3.0.0",
            name: meta.name,
            description: meta.description,
            attribution: meta.attribution,
            scheme: "xyz",
            tiles: [`${publicUrl}/${tileSetName}/{z}/{x}/{y}.${fileExtension}`],
            version: meta.version,
            bounds: [header.minLon, header.minLat, header.maxLon, header.maxLat],
            center: [header.centerLon, header.centerLat, header.centerZoom],
            minzoom: header.minZoom,
            maxzoom: header.maxZoom,
            vector_layers: meta.vector_layers,
        };
    }
}
