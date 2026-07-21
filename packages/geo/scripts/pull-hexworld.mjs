#!/usr/bin/env node
import { existsSync, mkdirSync, statSync } from "node:fs";
import { copyFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const TILES_DIR = resolve(HERE, "..", "tiles");

const ARCHIVE_SOURCE =
    process.env.AUTHENTIK_HEXWORLD_SOURCE ??
    "https://github.com/goauthentik/authentik/releases/download/hexworld-v1/hexworld.pmtiles";
const GLYPH_BASE =
    process.env.AUTHENTIK_HEXWORLD_GLYPHS ??
    "https://raw.githubusercontent.com/protomaps/basemaps-assets/main/fonts";
const FONTS = ["Noto Sans Regular", "Noto Sans Medium"];
const RANGES = ["0-255", "256-511"];

function isLocalPath(source) {
    return source.startsWith("/") || source.startsWith("./") || source.startsWith("../");
}

async function fetchTo(url, dest) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
    await writeFile(dest, Buffer.from(await res.arrayBuffer()));
    console.log(`fetched ${dest} (${statSync(dest).size} bytes)`);
}

mkdirSync(TILES_DIR, { recursive: true });

const archiveDest = resolve(TILES_DIR, "hexworld.pmtiles");
const sameFile = isLocalPath(ARCHIVE_SOURCE) && resolve(ARCHIVE_SOURCE) === archiveDest;
if (sameFile) {
    if (!existsSync(archiveDest)) throw new Error(`archive not found: ${archiveDest}`);
    console.log(`archive already at ${archiveDest}, skipping copy`);
} else if (isLocalPath(ARCHIVE_SOURCE)) {
    if (!existsSync(ARCHIVE_SOURCE)) throw new Error(`archive not found: ${ARCHIVE_SOURCE}`);
    await copyFile(ARCHIVE_SOURCE, archiveDest);
    console.log(`copied ${ARCHIVE_SOURCE} → ${archiveDest}`);
} else {
    await fetchTo(ARCHIVE_SOURCE, archiveDest);
}

for (const font of FONTS) {
    const dir = resolve(TILES_DIR, "fonts", font);
    mkdirSync(dir, { recursive: true });
    for (const range of RANGES) {
        await fetchTo(
            `${GLYPH_BASE}/${encodeURIComponent(font)}/${range}.pbf`,
            resolve(dir, `${range}.pbf`),
        );
    }
}
