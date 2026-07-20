import assert from "node:assert/strict";
import { gridDisk, latLngToCell } from "h3-js";
import { test } from "node:test";

import { borderEdges } from "../out/hexworld/borders.js";

test("cells inside the same country produce no border edges", () => {
    const berlin = latLngToCell(52.52, 13.405, 4);
    const cells = gridDisk(berlin, 1);
    const cellCountry = new Map(cells.map((c) => [c, "DE"]));
    const edges = borderEdges(cellCountry);
    assert.equal(edges.length, 0);
});

test("a pair of adjacent cells with different countries produces exactly one segment", () => {
    const berlin = latLngToCell(52.52, 13.405, 4);
    const [neighbor] = gridDisk(berlin, 1).filter((c) => c !== berlin);
    const cellCountry = new Map([
        [berlin, "DE"],
        [neighbor, "PL"],
    ]);
    const edges = borderEdges(cellCountry);
    assert.equal(edges.length, 1);
    const [line] = edges;
    assert.equal(line.type, "Feature");
    assert.equal(line.geometry.type, "LineString");
    assert.equal(line.geometry.coordinates.length, 2);
    assert.deepEqual([line.properties.a, line.properties.b].sort(), ["DE", "PL"]);
});

test("borderEdges dedupes reciprocal neighbor pairs", () => {
    const center = latLngToCell(52.52, 13.405, 4);
    const disk = gridDisk(center, 1);
    // Every 6 neighbors gets a different country. Each cell has all 6 neighbors
    // in its own gridDisk; naive iteration would emit each edge twice (once
    // from each side).
    const cellCountry = new Map();
    for (let i = 0; i < disk.length; i++) {
        cellCountry.set(disk[i], String.fromCharCode(65 + i, 65 + i));
    }
    const edges = borderEdges(cellCountry);
    // Every unordered adjacent pair in the disk contributes at most one edge.
    // The exact count depends on the disk's neighbor graph, but if any dupes
    // existed the count would double.
    const seen = new Set();
    for (const feature of edges) {
        const { a, b } = feature.properties;
        const key = [a, b].sort().join(":");
        assert.ok(!seen.has(key), `edge ${key} emitted twice`);
        seen.add(key);
    }
});

test("ocean neighbors (undefined country) do not produce border segments", () => {
    const berlin = latLngToCell(52.52, 13.405, 4);
    const cellCountry = new Map([[berlin, "DE"]]);
    // No entry for the surrounding cells — they're ocean/unassigned.
    const edges = borderEdges(cellCountry);
    assert.equal(edges.length, 0);
});
