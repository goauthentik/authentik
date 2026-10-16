/**
 * @file The hosted search endpoint: a Cloudflare Worker that answers `GET /search?q=` from the
 *   copy of the index in D1, with the same query code the browser runs against its own copy.
 *   The index lives in one of two table slots; `search_current` holds the current slot's name.
 *   A rebuild fills the other slot and flips the pointer, so this worker reads the pointer once
 *   per request and never sees a half-written index.
 */

import {
    INDEX_SLOTS,
    type IndexSlot,
    rewriteForSlot,
    SLOT_POINTER_TABLE,
} from "@goauthentik/docusaurus-theme/search/common";
import {
    search,
    type SearchDatabase,
    type SQLValue,
} from "@goauthentik/docusaurus-theme/search/query";

export interface Env {
    DB: D1Database;
}

/**
 * The most hits a caller may request.
 */
const MAX_LIMIT = 20;

/**
 * How long an edge cache and a browser may keep a response. A rebuild lands within this many
 * seconds of the pointer flip.
 */
const CACHE_SECONDS = 300;

const CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
};

function json(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: {
            "Content-Type": "application/json; charset=utf-8",
            ...CORS_HEADERS,
            ...headers,
        },
    });
}

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

async function handleSearch(url: URL, env: Env): Promise<Response> {
    const q = url.searchParams.get("q")?.trim() ?? "";

    if (q === "") return json({ error: "q is required" }, 400);

    const site = url.searchParams.get("site") ?? "";
    const limit = Math.min(Number(url.searchParams.get("limit") ?? 8) || 8, MAX_LIMIT);
    const slot = await currentSlot(env.DB);

    if (slot === null) return json({ error: "the index has not been imported" }, 503);

    const response = await search(slotDatabase(env.DB, slot), q, limit, site);

    return json(response, 200, {
        "Cache-Control": `public, max-age=${CACHE_SECONDS}, s-maxage=${CACHE_SECONDS}`,
    });
}

async function handleHealth(env: Env): Promise<Response> {
    const slot = await currentSlot(env.DB);

    if (slot === null) return json({ slot: null }, 503);

    // Written out rather than rewritten: `records` is a column here, and the rewrite renames the
    // word wherever it stands.
    const build = await env.DB.prepare(`SELECT commit_sha, records FROM build_${slot}`).first<{
        commit_sha: string;
        records: number;
    }>();

    return json({ slot, commit: build?.commit_sha ?? "", records: build?.records ?? 0 });
}

export default {
    async fetch(request: Request, env: Env, context: ExecutionContext): Promise<Response> {
        if (request.method === "OPTIONS") {
            return new Response(null, { status: 204, headers: CORS_HEADERS });
        }

        if (request.method !== "GET") {
            return json({ error: "method not allowed" }, 405, { Allow: "GET, OPTIONS" });
        }

        const url = new URL(request.url);

        if (url.pathname === "/health") return handleHealth(env);

        if (url.pathname !== "/search") return json({ error: "not found" }, 404);

        // Responses are cached at the edge by URL, so a repeated query costs no D1 read.
        const cache = caches.default;
        const cached = await cache.match(request);

        if (cached) return cached;

        const response = await handleSearch(url, env);

        if (response.ok) {
            context.waitUntil(cache.put(request, response.clone()));
        }

        return response;
    },
} satisfies ExportedHandler<Env>;
