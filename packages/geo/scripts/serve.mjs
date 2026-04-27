#!/usr/bin/env node
import { mkdirSync } from "node:fs";

import {
    IMAGE_TAG,
    SERVE_PORT,
    TILES_DIR,
    ensureImage,
    pickContainerEngine,
    run,
} from "./_runtime.mjs";

mkdirSync(TILES_DIR, { recursive: true });

const engine = pickContainerEngine();
await ensureImage(engine);

const args = [
    "run",
    "--rm",
    "-it",
    "-p",
    `${SERVE_PORT}:8484`,
    "-v",
    `${TILES_DIR}:/tiles:Z`,
    IMAGE_TAG,
    "serve",
    "/tiles",
    "--port",
    "8484",
    "--cors",
    "*",
];

console.log(`> ${engine} ${args.join(" ")}`);
await run(engine, args);
