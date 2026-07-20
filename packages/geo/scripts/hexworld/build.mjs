#!/usr/bin/env node
import { extractLabels } from "./extract-labels.mjs";

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, statSync, writeFileSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import { parseArgs } from "node:util";

import { HEX_BANDS } from "../../out/hexworld/bands.js";
import { borderEdges } from "../../out/hexworld/borders.js";
import {
    assignCountries,
    assignRegions,
    buildCountryIndex,
    buildRegionIndex,
} from "../../out/hexworld/countries.js";
import { capLocalities, placeFeature } from "../../out/hexworld/labels.js";
import { hexFeature, landCells } from "../../out/hexworld/land.js";

// Pinned Natural Earth release. Bump deliberately — every archive on the wire
// should be reproducible from a specific vector-data commit.
const NE_TAG = "v5.1.2";
const NE_BASE = `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/${NE_TAG}/geojson`;
const LAND_URL = `${NE_BASE}/ne_50m_land.geojson`;
const COUNTRIES_URL = `${NE_BASE}/ne_50m_admin_0_countries.geojson`;
// 10m — the 50m admin-1 dataset only covers nine countries. 10m gives all 241.
// Detail past the ~52 km res-4 cell gets collapsed to cell edges anyway, so
// the higher-res source doesn't cost anything at render time.
const REGIONS_URL = `${NE_BASE}/ne_10m_admin_1_states_provinces.geojson`;

const TILE_FLAGS = [
    "--force",
    "--no-feature-limit",
    "--no-tile-size-limit",
    "--no-tiny-polygon-reduction",
    "--detect-shared-borders",
];

const BORDER_TILE_FLAGS = ["--force", "--no-feature-limit", "--no-tile-size-limit"];

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
    for (const band of HEX_BANDS) {
        plan.push([
            "tippecanoe",
            ...BORDER_TILE_FLAGS,
            "-Z" + band.minzoom,
            "-z" + band.maxzoom,
            "-l",
            "borders",
            "-o",
            `${outDir}/borders-r${band.res}.pmtiles`,
            `${outDir}/borders-r${band.res}.geojsonl`,
        ]);
    }
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
        const bands = HEX_BANDS.filter((band) => band.res <= cut);
        plan.push([
            "tile-join",
            "--force",
            "--no-tile-size-limit",
            "-o",
            `${outDir}/hexworld-r${cut}.pmtiles`,
            ...bands.map((band) => `${outDir}/hex-r${band.res}.pmtiles`),
            ...bands.map((band) => `${outDir}/borders-r${band.res}.pmtiles`),
            `${outDir}/places.pmtiles`,
        ]);
    }
    return plan;
}

// Deliberately synchronous. An earlier async createWriteStream + .end() version
// looked fine but bit the places geojsonl step: the following spawnSync
// blocks the event loop, so the write stream never got a chance to drain and
// tippecanoe read an empty file. Fully-formed buffer, single syscall, no race.
function writeLines(path, features) {
    writeFileSync(path, features.map((feature) => JSON.stringify(feature)).join("\n") + "\n");
}

async function fetchIfMissing(url, dest) {
    if (existsSync(dest)) return;
    console.log(`Fetching ${url} → ${dest}`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`fetch failed: ${url} → HTTP ${res.status}`);
    await writeFile(dest, Buffer.from(await res.arrayBuffer()));
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
    await fetchIfMissing(LAND_URL, landPath);
    const land = JSON.parse(await readFile(landPath, "utf8"));

    const countriesPath = `${outDir}/ne_50m_admin_0_countries.geojson`;
    await fetchIfMissing(COUNTRIES_URL, countriesPath);
    const countries = JSON.parse(await readFile(countriesPath, "utf8"));
    const countryIndex = buildCountryIndex(countries);
    console.log(`countries: indexed ${countryIndex.entries.length} entries`);

    const regionsPath = `${outDir}/ne_10m_admin_1_states_provinces.geojson`;
    await fetchIfMissing(REGIONS_URL, regionsPath);
    const regions = JSON.parse(await readFile(regionsPath, "utf8"));
    const regionIndex = buildRegionIndex(regions);
    console.log(`regions: indexed ${regionIndex.entries.length} entries`);

    for (const band of HEX_BANDS) {
        const cells = landCells(land, band.res);
        const cellCountry = assignCountries(cells, countryIndex);
        const cellRegion = assignRegions(cells, regionIndex);
        console.log(
            `res ${band.res}: ${cells.size} land cells, ${cellCountry.size} country-tagged, ${cellRegion.size} region-tagged`,
        );
        writeLines(
            `${outDir}/hex-r${band.res}.geojsonl`,
            [...cells].map((cell) => hexFeature(cell, cellCountry.get(cell))),
        );
        const edges = borderEdges({ country: cellCountry, region: cellRegion });
        const level0 = edges.filter((e) => e.properties.level === 0).length;
        const level1 = edges.length - level0;
        console.log(`  borders: ${level0} country + ${level1} region`);
        writeLines(`${outDir}/borders-r${band.res}.geojsonl`, edges);
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
