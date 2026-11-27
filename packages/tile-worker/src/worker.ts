import { applyCors, type CorsOptions, preflightResponse } from "./cors.js";
import { TileFileExtensionMap } from "./files.js";
import { CloudflareWorkerPMTiles } from "./pmtiles.js";
import { TileSetNotFoundError } from "./r2-source.js";

import { TileType } from "pmtiles";

export interface Env {
    TILES_BUCKET: R2Bucket;
    TILES_PATH: string;
    ALLOWED_ORIGINS: string;
}

const TILE_PATTERN =
    /^\/(?<tileset>[a-zA-Z0-9_\-]+)\/(?<z>\d+)\/(?<x>\d+)\/(?<y>\d+)\.(?<ext>[a-z0-9]+)$/;
const META_PATTERN = /^\/(?<tileset>[a-zA-Z0-9_\-]+)\.json$/;

const handler: ExportedHandler<Env> = {
    async fetch(request, env, ctx) {
        const corsOptions: CorsOptions = {
            allowedOrigins: env.ALLOWED_ORIGINS ?? "*",
        };

        if (request.method === "OPTIONS") {
            return preflightResponse(request, corsOptions);
        }
        if (request.method !== "GET" && request.method !== "HEAD") {
            return finish(
                new Response("Method Not Allowed", { status: 405 }),
                request,
                corsOptions,
            );
        }

        const url = new URL(request.url);
        const cache = caches.default;
        const cached = await cache.match(request);
        if (cached) return cached;

        try {
            const tileMatch = TILE_PATTERN.exec(url.pathname);
            if (tileMatch?.groups) {
                const tileset = tileMatch.groups["tileset"]!;
                const z = Number(tileMatch.groups["z"]);
                const x = Number(tileMatch.groups["x"]);
                const y = Number(tileMatch.groups["y"]);
                const ext = tileMatch.groups["ext"]!;
                const response = await serveTile(env, tileset, z, x, y, ext);
                applyCors(request, response, corsOptions);
                if (response.ok) ctx.waitUntil(cache.put(request, response.clone()));
                return response;
            }

            const metaMatch = META_PATTERN.exec(url.pathname);
            if (metaMatch?.groups) {
                const tileset = metaMatch.groups["tileset"]!;
                const response = await serveMeta(env, url, tileset);
                applyCors(request, response, corsOptions);
                if (response.ok) ctx.waitUntil(cache.put(request, response.clone()));
                return response;
            }

            return finish(new Response("Not Found", { status: 404 }), request, corsOptions);
        } catch (error) {
            return finish(errorResponse(error), request, corsOptions);
        }
    },
};

export default handler;

async function serveTile(
    env: Env,
    tileset: string,
    z: number,
    x: number,
    y: number,
    ext: string,
): Promise<Response> {
    const tileType = TileFileExtensionMap.get(ext as never) ?? TileType.Unknown;
    if (tileType === TileType.Unknown) {
        return new Response(`Unknown tile extension: ${ext}`, { status: 400 });
    }

    const pm = CloudflareWorkerPMTiles.from({
        bucket: env.TILES_BUCKET,
        pathPrefix: env.TILES_PATH,
        tileSetName: tileset,
    });

    const tile = await pm.retrieveTile({ tileType, z, x, y });
    if (!tile) {
        return new Response(null, { status: 204 });
    }

    const headers = new Headers({
        "Content-Type": tile.contentType,
        "Cache-Control": tile.cacheControl ?? "public, max-age=86400, immutable",
    });
    if (tile.etag) headers.set("ETag", tile.etag);
    if (tile.expires) headers.set("Expires", tile.expires);

    return new Response(tile.data, { headers });
}

async function serveMeta(env: Env, url: URL, tileset: string): Promise<Response> {
    const pm = CloudflareWorkerPMTiles.from({
        bucket: env.TILES_BUCKET,
        pathPrefix: env.TILES_PATH,
        tileSetName: tileset,
    });
    const publicUrl = `${url.protocol}//${url.host}`;
    const meta = await pm.retrieveTileJSON(tileset, publicUrl);
    return new Response(JSON.stringify(meta), {
        headers: {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=86400",
        },
    });
}

function errorResponse(error: unknown): Response {
    if (error instanceof TileSetNotFoundError) {
        return new Response(error.message, { status: 404 });
    }
    if (error instanceof Error) {
        const status = (error as Error & { status?: number }).status;
        if (typeof status === "number") {
            return new Response(error.message, { status });
        }
        return new Response(`Internal error: ${error.message}`, { status: 500 });
    }
    return new Response("Internal error", { status: 500 });
}

function finish(response: Response, request: Request, options: CorsOptions): Response {
    applyCors(request, response, options);
    return response;
}
