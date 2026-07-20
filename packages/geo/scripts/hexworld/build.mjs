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
import { computeDetailZone } from "../../out/hexworld/detail-zone.js";
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

/**
 * Layout of the hex-band tippecanoe invocations. The `label` on each entry
 * describes the file the geojsonl for that slice lives at; the plan uses it
 * as the output pmtiles name too.
 */
function hexSlices() {
    // Res-3 → z0-2, res-4 → z3-6 come straight from HEX_BANDS. At z7-8 the
    // archive carries both a full res-4 base (visible outside the detail
    // zone) and a res-5 overlay (zone cells only, drawn on top).
    return [
        { label: "hex-r3", res: 3, minzoom: 0, maxzoom: 2 },
        { label: "hex-r4", res: 4, minzoom: 3, maxzoom: 6 },
        { label: "hex-r4-base", res: 4, minzoom: 7, maxzoom: 8 },
        { label: "hex-r5", res: 5, minzoom: 7, maxzoom: 8 },
    ];
}

function borderSlices() {
    return [
        { label: "borders-r3", res: 3, minzoom: 0, maxzoom: 2 },
        { label: "borders-r4", res: 4, minzoom: 3, maxzoom: 6 },
        { label: "borders-r4-base", res: 4, minzoom: 7, maxzoom: 8 },
        { label: "borders-r5", res: 5, minzoom: 7, maxzoom: 8 },
    ];
}

/** Ordered shell commands for the tiling stage. Pure — unit tested. */
export function buildPlan({ outDir, localities }) {
    const plan = [];
    for (const slice of hexSlices()) {
        plan.push([
            "tippecanoe",
            ...TILE_FLAGS,
            "-Z" + slice.minzoom,
            "-z" + slice.maxzoom,
            "-l",
            "hex",
            "-o",
            `${outDir}/${slice.label}.pmtiles`,
            `${outDir}/${slice.label}.geojsonl`,
        ]);
    }
    for (const slice of borderSlices()) {
        plan.push([
            "tippecanoe",
            ...BORDER_TILE_FLAGS,
            "-Z" + slice.minzoom,
            "-z" + slice.maxzoom,
            "-l",
            "borders",
            "-o",
            `${outDir}/${slice.label}.pmtiles`,
            `${outDir}/${slice.label}.geojsonl`,
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
        const wantedRes = HEX_BANDS.filter((band) => band.res <= cut).map((b) => b.res);
        const hexPieces = hexSlices()
            .filter((s) => wantedRes.includes(s.res))
            .map((s) => `${outDir}/${s.label}.pmtiles`);
        const borderPieces = borderSlices()
            .filter((s) => wantedRes.includes(s.res))
            .map((s) => `${outDir}/${s.label}.pmtiles`);
        plan.push([
            "tile-join",
            "--force",
            "--no-tile-size-limit",
            "-o",
            `${outDir}/hexworld-r${cut}.pmtiles`,
            ...hexPieces,
            ...borderPieces,
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

/**
 * At z7-8 the base fill is res-4 and the overlay is res-5 zone cells only.
 * Res-4 borders whose two endpoints both fall in the zone are invisible under
 * the overlay and get taken over by res-5 borders — skip them from the base
 * emission so they don't ship twice.
 */
function filterRes4BaseBorders(edges, zoneBaseCells) {
    if (!zoneBaseCells || zoneBaseCells.size === 0) return edges;
    return edges.filter((edge) => {
        const { aCell, bCell } = edge.properties;
        if (!aCell || !bCell) return true;
        return !(zoneBaseCells.has(aCell) && zoneBaseCells.has(bCell));
    });
}

async function main() {
    const { values } = parseArgs({
        options: {
            dump: { type: "string" },
            out: { type: "string", default: "tiles" },
            localities: { type: "string", default: "50000" },
            "detail-ring": { type: "string", default: "1" },
            "detail-min-pop": { type: "string", default: "0" },
            "dry-run": { type: "boolean", default: false },
        },
    });
    const outDir = values.out;
    const localities = Number(values.localities);
    const detailRing = Number(values["detail-ring"]);
    const detailMinPop = Number(values["detail-min-pop"]);
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

    const zone = computeDetailZone(kept, { ring: detailRing, minPop: detailMinPop });
    console.log(
        `detail zone: ${zone.seedCount} seed labels (min pop ${detailMinPop}) → ${zone.baseCells.size} res-4 base cells (~${((zone.baseCells.size / 76_800) * 100).toFixed(1)}% of land) × ring ${detailRing}`,
    );

    const perRes = new Map();
    for (const res of [3, 4, 5]) {
        const cells = landCells(land, res);
        const cellCountry = assignCountries(cells, countryIndex);
        const cellRegion = assignRegions(cells, regionIndex);
        console.log(
            `res ${res}: ${cells.size} land cells, ${cellCountry.size} country-tagged, ${cellRegion.size} region-tagged`,
        );
        const edges = borderEdges({ country: cellCountry, region: cellRegion, land: cells });
        const level0 = edges.filter((e) => e.properties.level === 0).length;
        const level1 = edges.length - level0;
        console.log(`  borders: ${level0} country/coast + ${level1} region`);
        perRes.set(res, { cells, cellCountry, cellRegion, edges });
    }

    // hex emission: one geojsonl per slice.
    for (const slice of hexSlices()) {
        const { cells, cellCountry } = perRes.get(slice.res);
        let emit = cells;
        if (slice.label === "hex-r5") {
            emit = new Set([...cells].filter((cell) => zone.detailCells.has(cell)));
        }
        const features = [...emit].map((cell) =>
            withResProp(hexFeature(cell, cellCountry.get(cell)), slice.res),
        );
        console.log(`  ${slice.label}: ${features.length} hexes`);
        writeLines(`${outDir}/${slice.label}.geojsonl`, features);
    }

    // borders emission.
    for (const slice of borderSlices()) {
        const { edges } = perRes.get(slice.res);
        let emit = edges;
        if (slice.label === "borders-r4-base") {
            // Skip res-4 borders whose both endpoints are inside the zone —
            // the res-5 overlay draws its own borders there.
            emit = filterRes4BaseBorders(edges, zone.baseCells);
        } else if (slice.label === "borders-r5") {
            // Keep only edges where both endpoints fall in the res-5 zone.
            emit = edges.filter((edge) => {
                const { aCell, bCell } = edge.properties;
                if (!aCell || !bCell) return false;
                return zone.detailCells.has(aCell) && zone.detailCells.has(bCell);
            });
        }
        console.log(`  ${slice.label}: ${emit.length} segments`);
        writeLines(
            `${outDir}/${slice.label}.geojsonl`,
            emit.map(stripCellProps),
        );
    }

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

function withResProp(feature, res) {
    return {
        ...feature,
        properties: { ...feature.properties, res },
    };
}

// The generator carries the H3 cell ids on border features so downstream
// filtering (res-4 base zone skip, res-5 zone keep) can key off them. Strip
// them before tippecanoe reads the geojsonl so the shipped archive stays
// small — the runtime style doesn't use them.
function stripCellProps(edge) {
    const { aCell: _aCell, bCell: _bCell, ...properties } = edge.properties;
    return { ...edge, properties };
}

const invokedDirectly = process.argv[1]?.endsWith("build.mjs");
if (invokedDirectly) {
    main().catch((error) => {
        console.error(error);
        process.exit(1);
    });
}
