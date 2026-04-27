#!/usr/bin/env node
import { mkdirSync } from "node:fs";

import { IMAGE_TAG, TILES_DIR, ensureImage, pickContainerEngine, run } from "./_runtime.mjs";

const SOURCE_URL = process.env.AUTHENTIK_TILES_SOURCE_URL;
const OUTPUT = process.env.AUTHENTIK_TILES_OUTPUT ?? "world.pmtiles";
const BBOX = process.env.AUTHENTIK_TILES_BBOX ?? "-180,-85,180,85";
const MAXZOOM = process.env.AUTHENTIK_TILES_MAXZOOM ?? "6";
const MINZOOM = process.env.AUTHENTIK_TILES_MINZOOM ?? "0";

if (!SOURCE_URL) {
    console.error("AUTHENTIK_TILES_SOURCE_URL is required.");
    console.error("Set it to a Protomaps planet build URL or a regional .pmtiles archive.");
    console.error("Example: https://build.protomaps.com/<YYYYMMDD>.pmtiles");
    process.exit(1);
}

mkdirSync(TILES_DIR, { recursive: true });

const engine = pickContainerEngine();
await ensureImage(engine);

const args = [
    "run",
    "--rm",
    "-v",
    `${TILES_DIR}:/tiles:Z`,
    IMAGE_TAG,
    "extract",
    SOURCE_URL,
    `/tiles/${OUTPUT}`,
    "--bbox",
    BBOX,
    "--minzoom",
    MINZOOM,
    "--maxzoom",
    MAXZOOM,
];

console.log(`> ${engine} ${args.join(" ")}`);
await run(engine, args);
console.log(`Wrote ${OUTPUT} to ${TILES_DIR}`);
