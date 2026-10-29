import { borderEdges } from "../src/borders.ts";

import { gridDisk, latLngToCell } from "h3-js";
import { expect, test } from "vitest";

test("cells inside the same country produce no border edges", () => {
    const berlin = latLngToCell(52.52, 13.405, 4);
    const cells = gridDisk(berlin, 1);
    const country = new Map(cells.map((c) => [c, "DE"]));
    const edges = borderEdges({ country });
    expect(edges.length).toBe(0);
});

test("a cross-country neighbor pair emits exactly one level-0 segment", () => {
    const berlin = latLngToCell(52.52, 13.405, 4);
    const [neighbor] = gridDisk(berlin, 1).filter((c) => c !== berlin);
    const country = new Map([
        [berlin, "DE"],
        [neighbor, "PL"],
    ]);
    const edges = borderEdges({ country });
    expect(edges.length).toBe(1);
    const [line] = edges;
    expect(line.type).toBe("Feature");
    expect(line.geometry.type).toBe("LineString");
    expect(line.geometry.coordinates.length).toBe(2);
    expect(line.properties.level).toBe(0);
    expect([line.properties.a, line.properties.b].sort()).toStrictEqual(["DE", "PL"]);
});

test("cross-region neighbors within the same country emit level-1 segments", () => {
    const denver = latLngToCell(39.74, -104.99, 4);
    const [neighbor] = gridDisk(denver, 1).filter((c) => c !== denver);
    const country = new Map([
        [denver, "US"],
        [neighbor, "US"],
    ]);
    const region = new Map([
        [denver, "US-CO"],
        [neighbor, "US-NE"],
    ]);
    const edges = borderEdges({ country, region });
    expect(edges.length).toBe(1);
    const [line] = edges;
    expect(line.properties.level).toBe(1);
    expect([line.properties.a, line.properties.b].sort()).toStrictEqual(["US-CO", "US-NE"]);
});

test("country borders take precedence over region borders when both differ", () => {
    const cell = latLngToCell(52.52, 13.405, 4);
    const [neighbor] = gridDisk(cell, 1).filter((c) => c !== cell);
    const country = new Map([
        [cell, "DE"],
        [neighbor, "PL"],
    ]);
    // Region codes also differ, but the coincident country border wins.
    const region = new Map([
        [cell, "DE-BE"],
        [neighbor, "PL-14"],
    ]);
    const edges = borderEdges({ country, region });
    expect(edges.length).toBe(1);
    expect(edges[0].properties.level).toBe(0);
    expect([edges[0].properties.a, edges[0].properties.b].sort()).toStrictEqual(["DE", "PL"]);
});

test("borderEdges dedupes reciprocal neighbor pairs at either level", () => {
    const center = latLngToCell(52.52, 13.405, 4);
    const disk = gridDisk(center, 1);
    const country = new Map();
    const region = new Map();
    for (let i = 0; i < disk.length; i++) {
        country.set(disk[i], "US");
        region.set(disk[i], String.fromCharCode(65 + i, 65 + i));
    }
    const edges = borderEdges({ country, region });
    const seen = new Set();
    for (const feature of edges) {
        const { a, b } = feature.properties;
        const key = [a, b].sort().join(":");
        expect(!seen.has(key), `edge ${key} emitted twice`).toBeTruthy();
        seen.add(key);
    }
});

test("neighbors with unassigned country skip border emission", () => {
    const berlin = latLngToCell(52.52, 13.405, 4);
    const country = new Map([[berlin, "DE"]]);
    // No entries for surrounding cells — treated as ocean.
    const edges = borderEdges({ country });
    expect(edges.length).toBe(0);
});

test("region borders skip cells missing a region code even when country matches", () => {
    const denver = latLngToCell(39.74, -104.99, 4);
    const [neighbor] = gridDisk(denver, 1).filter((c) => c !== denver);
    const country = new Map([
        [denver, "US"],
        [neighbor, "US"],
    ]);
    // Only one cell has a region code — the other should not trigger a border.
    const region = new Map([[denver, "US-CO"]]);
    const edges = borderEdges({ country, region });
    expect(edges.length).toBe(0);
});

test("coastal edges emit at level 0 for land cells whose neighbors are not land", () => {
    // A single land cell in the middle of the ocean: every one of its six
    // neighbors is ocean, and every shared edge should ship as a coastal
    // segment at level 0.
    const island = latLngToCell(0, 0, 4);
    const land = new Set([island]);
    const country = new Map([[island, "XX"]]);
    const edges = borderEdges({ country, land });
    expect(edges.length).toBe(6);
    for (const feature of edges) {
        expect(feature.properties.level).toBe(0);
        // One side is the land country code, the other is the empty ocean
        // marker — order depends on which cell id sorts first.
        expect([feature.properties.a, feature.properties.b].sort()).toStrictEqual(["", "XX"]);
    }
});

test("coastal edges dedupe against country-vs-country borders", () => {
    // Two adjacent land cells in different countries. Between them: one
    // level-0 country border. Around them: coastal edges to ocean. The
    // shared edge must not appear twice (once country, once coastal).
    const cell = latLngToCell(0, 0, 4);
    const [neighbor] = gridDisk(cell, 1).filter((c) => c !== cell);
    const land = new Set([cell, neighbor]);
    const country = new Map([
        [cell, "AA"],
        [neighbor, "BB"],
    ]);
    const edges = borderEdges({ country, land });
    // Each cell has 6 neighbors; one is the other land cell, five are ocean.
    // Total = 1 country border + 10 coastal = 11.
    expect(edges.length).toBe(11);
    const seen = new Set();
    for (const feature of edges) {
        const key = JSON.stringify(feature.geometry.coordinates);
        expect(!seen.has(key), "duplicate geometry emitted").toBeTruthy();
        seen.add(key);
    }
    const countryBorders = edges.filter((e) => e.properties.a !== "" && e.properties.b !== "");
    expect(countryBorders.length).toBe(1);
    expect([countryBorders[0].properties.a, countryBorders[0].properties.b].sort()).toStrictEqual([
        "AA",
        "BB",
    ]);
});

test("land cells outside every country still get coastal edges", () => {
    // A remote island the country point-in-polygon check might miss (no
    // country entry). It should still ship its perimeter as level-0 ocean
    // edges with an empty country code on both sides.
    const island = latLngToCell(-70, 0, 4);
    const land = new Set([island]);
    const country = new Map();
    const edges = borderEdges({ country, land });
    expect(edges.length).toBe(6);
    for (const feature of edges) {
        expect(feature.properties.level).toBe(0);
        expect(feature.properties.a).toBe("");
        expect(feature.properties.b).toBe("");
    }
});
