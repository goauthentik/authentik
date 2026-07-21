#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, statSync, writeFileSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import { parseArgs } from "node:util";

import { extractLabels } from "./extract-labels.ts";

import {
    assignCountries,
    assignRegions,
    borderEdges,
    buildCountryIndex,
    buildRegionIndex,
    capLocalities,
    computeDetailZone,
    hexFeature,
    landCells,
    MAX_BAND_ZOOM,
    placeFeature,
} from "@goauthentik/geo/hexworld";

import type { Feature } from "geojson";

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

function withResProp(feature: Feature, res: number): Feature {
    return {
        ...feature,
        properties: { ...feature.properties, res },
    };
}

function stripCellProps(edge: EdgeFeature): EdgeFeature {
    const { aCell: _aCell, bCell: _bCell, ...properties } = edge.properties;
    return { ...edge, properties };
}

const TILE_FLAGS = [
    "--force",
    "--no-feature-limit",
    "--no-tile-size-limit",
    "--no-tiny-polygon-reduction",
    "--detect-shared-borders",
];

const BORDER_TILE_FLAGS = ["--force", "--no-feature-limit", "--no-tile-size-limit"];

export interface HexSlice {
    label: string;
    res: number;
    minzoom: number;
    maxzoom: number;
}

/**
 * Layout of the hex-band tippecanoe invocations. The `label` on each entry
 * describes the file the geojsonl for that slice lives at; the plan uses it
 * as the output pmtiles name too.
 */
function hexSlices(): HexSlice[] {
    // Res-3 → z0-2, res-4 → z3-6 come straight from HEX_BANDS. At z7-8 the
    // archive carries both a full res-4 base (visible outside the detail
    // zone) and a res-5 overlay (zone cells only, drawn on top).
    // The `-fade` slices carry res-3 geometry one tile zoom into the res-4
    // band: the style cross-fades the grids by `res` across that window
    // instead of letting them pop at the boundary. z7 needs no fade slice —
    // the res-4 base persists there and the res-5 overlay fades in over it.
    return [
        { label: "hex-r3", res: 3, minzoom: 0, maxzoom: 2 },
        { label: "hex-r3-fade", res: 3, minzoom: 3, maxzoom: 3 },
        { label: "hex-r4", res: 4, minzoom: 3, maxzoom: 6 },
        { label: "hex-r4-base", res: 4, minzoom: 7, maxzoom: 7 },
        { label: "hex-r5", res: 5, minzoom: 7, maxzoom: 7 },
    ];
}

function borderSlices(): HexSlice[] {
    return [
        { label: "borders-r3", res: 3, minzoom: 0, maxzoom: 2 },
        { label: "borders-r3-fade", res: 3, minzoom: 3, maxzoom: 3 },
        { label: "borders-r4", res: 4, minzoom: 3, maxzoom: 6 },
        { label: "borders-r4-base", res: 4, minzoom: 7, maxzoom: 7 },
        { label: "borders-r5", res: 5, minzoom: 7, maxzoom: 7 },
    ];
}

export interface BuildPlanOptions {
    outDir: string;
    localities: number;
}

/** Ordered shell commands for the tiling stage. Pure — unit tested. */
export function buildPlan({ outDir, localities }: BuildPlanOptions): string[][] {
    const plan: string[][] = [];

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
        "-z" + MAX_BAND_ZOOM,
        "-l",
        "places",
        "-o",
        `${outDir}/places.pmtiles`,
        `${outDir}/places-${localities}.geojsonl`,
    ]);

    // `detail` is the shipped archive: every slice, including the zoned res-5
    // overlay and the res-4 base it sits on. `plain` drops the whole z7 detail
    // band for anyone who wants the small archive. Filtering by `res <= cut`
    // was wrong once the detail band existed — it silently dropped the res-5
    // overlay AND left z7 with a base fill and no borders.

    for (const cut of ["detail", "plain"]) {
        const keep = (s: HexSlice) => cut === "detail" || s.minzoom < 7;

        const hexPieces = hexSlices()
            .filter(keep)
            .map((s) => `${outDir}/${s.label}.pmtiles`);

        const borderPieces = borderSlices()
            .filter(keep)
            .map((s) => `${outDir}/${s.label}.pmtiles`);

        plan.push([
            "tile-join",
            "--force",
            "--no-tile-size-limit",
            "-o",
            `${outDir}/hexworld-${cut}.pmtiles`,
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
function writeLines(path: string, features: unknown[]) {
    writeFileSync(path, features.map((feature) => JSON.stringify(feature)).join("\n") + "\n");
}

async function fetchIfMissing(url: string, dest: string): Promise<void> {
    if (existsSync(dest)) {
        return;
    }

    console.log(`Fetching ${url} → ${dest}`);

    const res = await fetch(url);

    if (!res.ok) {
        throw new Error(`fetch failed: ${url} → HTTP ${res.status}`);
    }

    await writeFile(dest, Buffer.from(await res.arrayBuffer()));
}

interface EdgeFeature extends Feature {
    properties: {
        level: number;
        aCell?: string;
        bCell?: string;
    };
}

/**
 * At z7-8 the base fill is res-4 and the overlay is res-5 zone cells only.
 * Res-4 borders whose two endpoints both fall in the zone are invisible under
 * the overlay and get taken over by res-5 borders — skip them from the base
 * emission so they don't ship twice.
 */
function filterRes4BaseBorders(edges: EdgeFeature[], zoneBaseCells: Set<string>): EdgeFeature[] {
    if (!zoneBaseCells || zoneBaseCells.size === 0) {
        return edges;
    }

    return edges.filter((edge) => {
        const { aCell, bCell } = edge.properties;

        if (!aCell || !bCell) {
            return true;
        }

        return !(zoneBaseCells.has(aCell) && zoneBaseCells.has(bCell));
    });
}

export interface HexCellData {
    cells: Set<string>;
    cellCountry: Map<string, string>;
    cellRegion: Map<string, string>;
    edges: EdgeFeature[];
}

async function main() {
    const { values } = parseArgs({
        options: {
            "dump": { type: "string" },
            "out": { type: "string", default: "tiles" },
            "localities": { type: "string", default: "50000" },
            "detail-ring": { type: "string", default: "1" },
            "detail-min-pop": { type: "string", default: "50000" },
            "dry-run": { type: "boolean", default: false },
        },
    });

    const outDir = values.out;
    const localities = Number(values.localities);
    const detailRing = Number(values["detail-ring"]);
    const detailMinPop = Number(values["detail-min-pop"]);

    mkdirSync(outDir, { recursive: true });

    if (values["dry-run"]) {
        for (const cmd of buildPlan({ outDir, localities })) {
            console.log(cmd.join(" "));
        }

        return;
    }

    if (!values.dump) {
        throw new Error("--dump <planet-z8.pmtiles> is required");
    }

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

    const hexCellDataByResolution = new Map<number, HexCellData>();

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
        hexCellDataByResolution.set(res, { cells, cellCountry, cellRegion, edges });
    }

    // hex emission: one geojsonl per slice.

    for (const slice of hexSlices()) {
        const { cells, cellCountry } = hexCellDataByResolution.get(slice.res)!;
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
        const { edges } = hexCellDataByResolution.get(slice.res)!;

        let emit = edges;

        if (slice.label === "borders-r3-fade") {
            // Region borders were never visible in the res-3 band (the layer
            // starts at z3); only country/coast lines take part in the fade.
            emit = edges.filter((edge) => edge.properties.level === 0);
        } else if (slice.label === "borders-r4-base") {
            // Skip res-4 borders whose both endpoints are inside the zone —
            // the res-5 overlay draws its own borders there.
            emit = filterRes4BaseBorders(edges, zone.baseCells);
        } else if (slice.label === "borders-r5") {
            // Keep only edges where both endpoints fall in the res-5 zone.
            emit = edges.filter((edge) => {
                const { aCell, bCell } = edge.properties;

                if (!aCell || !bCell) {
                    return false;
                }

                return zone.detailCells.has(aCell) && zone.detailCells.has(bCell);
            });
        }

        console.log(`  ${slice.label}: ${emit.length} segments`);

        // Border features need `res` too — the band cross-fade ramps their
        // opacity by resolution just like the hex fills.
        writeLines(
            `${outDir}/${slice.label}.geojsonl`,
            emit.map((edge) => withResProp(stripCellProps(edge), slice.res)),
        );
    }

    for (const cmd of buildPlan({ outDir, localities })) {
        console.log(`> ${cmd.join(" ")}`);

        const result = spawnSync(cmd[0]!, cmd.slice(1), { stdio: "inherit" });

        if (result.status !== 0) {
            throw new Error(`${cmd[0]} exited ${result.status}`);
        }
    }

    for (const cut of ["detail", "plain"]) {
        const size = statSync(`${outDir}/hexworld-${cut}.pmtiles`).size;

        console.log(`hexworld-${cut}.pmtiles  ${(size / 1024 / 1024).toFixed(1)} MB`);
    }
}

if (import.meta.main) {
    main().catch((error) => {
        console.error(error);
        process.exit(1);
    });
}
