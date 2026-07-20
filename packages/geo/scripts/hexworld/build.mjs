#!/usr/bin/env node
import { extractLabels } from "./extract-labels.mjs";

import { spawnSync } from "node:child_process";
import { createWriteStream, existsSync, mkdirSync, statSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import { parseArgs } from "node:util";

import { HEX_BANDS } from "../../out/hexworld/bands.js";
import { capLocalities, placeFeature } from "../../out/hexworld/labels.js";
import { hexFeature, landCells } from "../../out/hexworld/land.js";

const LAND_URL =
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson";

const TILE_FLAGS = [
    "--force",
    "--no-feature-limit",
    "--no-tile-size-limit",
    "--no-tiny-polygon-reduction",
    "--detect-shared-borders",
];

/** Ordered shell commands for the tiling stage. Pure — unit tested. */
export function buildPlan({ outDir, localities }) {
    const plan = HEX_BANDS.map((band) => [
        "tippecanoe",
        ...TILE_FLAGS,
        "-Z" + band.minzoom,
        "-z" + band.maxzoom,
        "-l",
        "hex",
        "-o",
        `${outDir}/hex-r${band.res}.pmtiles`,
        `${outDir}/hex-r${band.res}.geojsonl`,
    ]);
    plan.push([
        "tippecanoe",
        "--force",
        "--no-feature-limit",
        "--no-tile-size-limit",
        "-r1",
        "-Z0",
        "-z8",
        "-l",
        "places",
        "-o",
        `${outDir}/places.pmtiles`,
        `${outDir}/places-${localities}.geojsonl`,
    ]);
    for (const cut of [4, 5]) {
        plan.push([
            "tile-join",
            "--force",
            "--no-tile-size-limit",
            "-o",
            `${outDir}/hexworld-r${cut}.pmtiles`,
            ...HEX_BANDS.filter((band) => band.res <= cut).map(
                (band) => `${outDir}/hex-r${band.res}.pmtiles`,
            ),
            `${outDir}/places.pmtiles`,
        ]);
    }
    return plan;
}

function writeLines(path, features) {
    const stream = createWriteStream(path);
    for (const feature of features) stream.write(JSON.stringify(feature) + "\n");
    stream.end();
}

async function main() {
    const { values } = parseArgs({
        options: {
            dump: { type: "string" },
            out: { type: "string", default: "tiles" },
            localities: { type: "string", default: "15000" },
            "dry-run": { type: "boolean", default: false },
        },
    });
    const outDir = values.out;
    const localities = Number(values.localities);
    mkdirSync(outDir, { recursive: true });

    if (values["dry-run"]) {
        for (const cmd of buildPlan({ outDir, localities })) console.log(cmd.join(" "));
        return;
    }
    if (!values.dump) throw new Error("--dump <planet-z8.pmtiles> is required");

    const landPath = `${outDir}/ne_50m_land.geojson`;
    if (!existsSync(landPath)) {
        console.log(`Fetching Natural Earth land → ${landPath}`);
        const res = await fetch(LAND_URL);
        if (!res.ok) throw new Error(`NE fetch failed: ${res.status}`);
        await writeFile(landPath, Buffer.from(await res.arrayBuffer()));
    }
    const land = JSON.parse(await readFile(landPath, "utf8"));

    for (const band of HEX_BANDS) {
        const cells = landCells(land, band.res);
        console.log(`res ${band.res}: ${cells.size} land cells`);
        writeLines(
            `${outDir}/hex-r${band.res}.geojsonl`,
            [...cells].map((cell) => hexFeature(cell)),
        );
    }

    console.log(`Extracting labels from ${values.dump} …`);
    const allPlaces = await extractLabels(values.dump, {
        onProgress: (tiles, count) => console.log(`  ${tiles} tiles decoded, ${count} raw places`),
    });
    const kept = capLocalities(allPlaces, localities);
    console.log(`labels: ${allPlaces.length} deduped → ${kept.length} kept`);
    writeLines(
        `${outDir}/places-${localities}.geojsonl`,
        kept.map((place) => placeFeature(place)),
    );

    for (const cmd of buildPlan({ outDir, localities })) {
        console.log(`> ${cmd.join(" ")}`);
        const result = spawnSync(cmd[0], cmd.slice(1), { stdio: "inherit" });
        if (result.status !== 0) throw new Error(`${cmd[0]} exited ${result.status}`);
    }

    for (const cut of [4, 5]) {
        const size = statSync(`${outDir}/hexworld-r${cut}.pmtiles`).size;
        console.log(`hexworld-r${cut}.pmtiles  ${(size / 1024 / 1024).toFixed(1)} MB`);
    }
}

const invokedDirectly = process.argv[1]?.endsWith("build.mjs");
if (invokedDirectly) {
    main().catch((error) => {
        console.error(error);
        process.exit(1);
    });
}
