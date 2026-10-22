#!/usr/bin/env node
/**
 * @file Build `authentik-asn.mmdb` from RIPE RIS routing dumps and RIPE's AS name list.
 */

import { existsSync, mkdirSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { parseArgs } from "node:util";
import { gunzipSync } from "node:zlib";

import { buildASNDatabase } from "../src/asn/build.ts";
import {
    AS_NAMES,
    RIS_DUMP_IPV4,
    RIS_DUMP_IPV6,
    parseASNames,
    selectRoutes,
} from "../src/asn/sources.ts";

import { type AsnResponse, Reader } from "mmdb-lib";

async function fetchSource(url: string, cacheDir: string, refresh: boolean): Promise<string> {
    const path = resolve(cacheDir, basename(url));
    if (refresh || !existsSync(path)) {
        const res = await fetch(url, {
            headers: { "User-Agent": "authentik-geo (+https://goauthentik.io)" },
        });
        if (!res.ok) {
            throw new Error(`${url} → HTTP ${res.status}`);
        }
        await writeFile(path, Buffer.from(await res.arrayBuffer()));
        console.log(`fetched ${url}`);
    }
    const raw = await readFile(path);
    return (url.endsWith(".gz") ? gunzipSync(raw) : raw).toString("utf8");
}

/**
 * Lookups every valid build resolves.
 */
const EXPECTED_ORIGINS: Record<string, number> = {
    "8.8.8.8": 15169,
    "1.1.1.1": 13335,
    "2001:4860:4860::8888": 15169,
};
const MIN_ROUTES = 1_000_000;

function verify(database: Uint8Array, routes: number): void {
    if (routes < MIN_ROUTES) {
        throw new Error(`Only ${routes} routes, expected at least ${MIN_ROUTES}`);
    }
    const reader = new Reader<AsnResponse>(Buffer.from(database));
    for (const [ip, origin] of Object.entries(EXPECTED_ORIGINS)) {
        const found = reader.get(ip)?.autonomous_system_number;
        if (found !== origin) {
            throw new Error(`${ip} resolved to AS${found}, expected AS${origin}`);
        }
    }
}

async function main() {
    const { values } = parseArgs({
        options: {
            "out": { type: "string", default: "out/authentik-asn.mmdb" },
            "cache": { type: "string", default: "out/sources" },
            "refresh": { type: "boolean", default: false },
            "min-peers": { type: "string" },
        },
    });
    mkdirSync(values.cache, { recursive: true });

    const [ipv4, ipv6, asNames] = await Promise.all(
        [RIS_DUMP_IPV4, RIS_DUMP_IPV6, AS_NAMES].map((url) =>
            fetchSource(url, values.cache, values.refresh),
        ),
    );
    const filter = values["min-peers"] ? { minPeers: Number(values["min-peers"]) } : {};
    const routes = [ipv4!, ipv6!].flatMap((dump) => selectRoutes(dump.split("\n"), filter));
    const names = parseASNames(asNames!.split("\n"));
    const database = buildASNDatabase(routes, names);
    verify(database, routes.length);

    mkdirSync(resolve(values.out, ".."), { recursive: true });
    await writeFile(values.out, database);
    console.log(
        `wrote ${values.out}: ${routes.length} routes, ${names.size} names, ${(database.length / 1e6).toFixed(1)} MB`,
    );
}

await main();
