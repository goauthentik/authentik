/**
 * @file The hosted search endpoint: a Cloudflare Worker that answers `GET /search?q=` from the
 *   copy of the index in D1, with the same query code the browser runs against its own copy.
 *   The index lives in one of two table slots; `search_current` holds the current slot's name.
 *   A rebuild fills the other slot and flips the pointer, so this worker reads the pointer once
 *   per request and never sees a half-written index.
 */

import { allowedOrigin } from "./origins.ts";

import {
    INDEX_SLOTS,
    type IndexSlot,
    rewriteForSlot,
    SLOT_POINTER_TABLE,
} from "@goauthentik/docusaurus-theme/search/common";
import {
    DEFAULT_LIMIT,
    search,
    type SearchDatabase,
    type SQLValue,
} from "@goauthentik/docusaurus-theme/search/query";

import { Hono } from "hono";
import { cors } from "hono/cors";

export interface Env {
    DB: D1Database;
}

/**
 * How long an edge cache and a browser may keep a response. A rebuild lands within this many
 * seconds of the pointer flip.
 */
const CACHE_SECONDS = 300;

/**
 * The edge cache that holds search responses, keyed by URL.
 */
const SEARCH_CACHE = "docs-search";

function isSlot(value: unknown): value is IndexSlot {
    return typeof value === "string" && (INDEX_SLOTS as readonly string[]).includes(value);
}

/**
 * The slot the pointer names, or `null` before the first import.
 */
async function currentSlot(db: D1Database): Promise<IndexSlot | null> {
    try {
        const row = await db
            .prepare(`SELECT slot FROM ${SLOT_POINTER_TABLE}`)
            .first<{ slot: unknown }>();

        return row !== null && isSlot(row.slot) ? row.slot : null;
    } catch {
        return null;
    }
}

/**
 * The query code's view of D1: every statement runs against `slot`'s tables.
 */
function slotDatabase(db: D1Database, slot: IndexSlot): SearchDatabase {
    return {
        async query(sql, parameters = []) {
            const bound = parameters.map((value) =>
                typeof value === "bigint" ? Number(value) : value,
            ) as (string | number | Uint8Array | null)[];

            const result = await db
                .prepare(rewriteForSlot(sql, slot))
                .bind(...bound)
                .all<Record<string, SQLValue>>();

            return result.results;
        },
    };
}

const app = new Hono<{ Bindings: Env }>();

app.use(
    cors({
        origin: (origin) => allowedOrigin(origin),
        allowMethods: ["GET", "OPTIONS"],
        maxAge: 86400,
    }),
);

app.get("/health", async (c) => {
    const slot = await currentSlot(c.env.DB);

    if (slot === null) return c.json({ slot: null }, 503);

    // Written out rather than rewritten: `records` is a column here, and the rewrite renames the
    // word wherever it stands.
    const build = await c.env.DB.prepare(`SELECT commit_sha, records FROM build_${slot}`).first<{
        commit_sha: string;
        records: number;
    }>();

    return c.json({ slot, commit: build?.commit_sha ?? "", records: build?.records ?? 0 });
});

app.get("/search", async (c) => {
    const q = c.req.query("q")?.trim() ?? "";

    if (q === "") return c.json({ error: "q is required" }, 400);

    // Responses are cached at the edge by URL, so a repeated query costs no D1 read. The cached
    // copy is built here without the CORS headers: `cors` set them on the context before this
    // handler ran, and Hono adds them to whatever the handler returns, so a cached response
    // names the requesting origin rather than the one that filled the cache.
    const cache = await caches.open(SEARCH_CACHE);
    const key = new Request(c.req.url, { method: "GET" });
    const cached = await cache.match(key);

    if (cached) return new Response(cached.body, cached);

    const site = c.req.query("site") ?? "";
    // `search` bounds the limit to its own range.
    const limit = Number(c.req.query("limit")) || DEFAULT_LIMIT;
    const slot = await currentSlot(c.env.DB);

    if (slot === null) return c.json({ error: "the index has not been imported" }, 503);

    const response = Response.json(await search(slotDatabase(c.env.DB, slot), q, limit, site), {
        headers: {
            "Cache-Control": `public, max-age=${CACHE_SECONDS}, s-maxage=${CACHE_SECONDS}`,
        },
    });

    c.executionCtx.waitUntil(cache.put(key, response.clone()));

    return response;
});

app.notFound((c) => c.json({ error: "not found" }, 404));

export default app;
