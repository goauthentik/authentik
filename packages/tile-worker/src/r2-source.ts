import { EtagMismatch, type RangeResponse, type Source } from "pmtiles";

export interface R2SourceConfig {
    bucket: R2Bucket;
    pathPrefix: string;
    tileSetName: string;
}

export class TileSetNotFoundError extends Error {
    constructor(key: string) {
        super(`Tile set not found in R2: ${key}`);
        this.name = "TileSetNotFoundError";
    }
}

/**
 * PMTiles {@link Source} implementation backed by Cloudflare R2.
 * Each tile coordinate translates to a byte-range read against the
 * archive object stored at `<pathPrefix>/<tileSetName>.pmtiles`.
 */
export class R2Source implements Source {
    readonly key: string;

    constructor(private readonly config: R2SourceConfig) {
        if (!config.bucket) throw new Error("R2Source requires a bucket binding");
        if (!config.tileSetName) throw new Error("R2Source requires a tileSetName");
        const trimmedPrefix = (config.pathPrefix ?? "").replace(/^\/|\/$/g, "");
        this.key = trimmedPrefix
            ? `${trimmedPrefix}/${config.tileSetName}.pmtiles`
            : `${config.tileSetName}.pmtiles`;
    }

    getKey(): string {
        return this.config.tileSetName;
    }

    async getBytes(
        offset: number,
        length: number,
        _signal?: AbortSignal,
        etag?: string,
    ): Promise<RangeResponse> {
        const response = await this.config.bucket.get(this.key, {
            range: { offset, length },
            onlyIf: etag ? { etagMatches: etag } : undefined,
        });

        if (!response) {
            throw new TileSetNotFoundError(this.key);
        }
        if (!("body" in response)) {
            // R2 returned a precondition object rather than the body —
            // pmtiles signals via EtagMismatch so the cache layer retries.
            throw new EtagMismatch();
        }

        return {
            data: await response.arrayBuffer(),
            etag: response.etag,
            cacheControl: response.httpMetadata?.cacheControl,
            expires: response.httpMetadata?.cacheExpiry?.toISOString(),
        };
    }
}
