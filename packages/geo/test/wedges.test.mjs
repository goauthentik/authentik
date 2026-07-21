import assert from "node:assert/strict";
import { test } from "node:test";

import { binEvents, buildEventFeatures } from "../out/hexworld/wedges.js";

import { cellToBoundary, getHexagonEdgeLengthAvg, UNITS } from "h3-js";

const BERLIN = { lat: 52.52, lon: 13.405 };
const PRAGUE = { lat: 50.075, lon: 14.437 };

test("binEvents tallies per cell and per action, defaulting to other", () => {
    const bins = binEvents(
        [
            { ...BERLIN, action: "login" },
            { ...BERLIN, action: "login" },
            { ...BERLIN, action: "login_failed" },
            { ...BERLIN },
            { ...PRAGUE, action: "logout" },
        ],
        2,
    );
    assert.equal(bins.size, 2);
    const berlin = [...bins.values()].find((bin) => bin.total === 4);
    assert.ok(berlin, "expected a 4-event bin for Berlin");
    assert.equal(berlin.counts.get("login"), 2);
    assert.equal(berlin.counts.get("login_failed"), 1);
    assert.equal(berlin.counts.get("other"), 1);
});

test("binEvents uses the zoom band resolution (coarser bins at world zoom)", () => {
    const close = [
        { lat: 52.52, lon: 13.405, action: "login" },
        { lat: 52.6, lon: 13.6, action: "login" },
    ];
    const world = binEvents(close, 0); // res 3
    const regional = binEvents(close, 8); // res 5
    assert.equal(world.size, 1);
    assert.equal(regional.size, 2);
});

/** Planar shoelace area on a closed [lng, lat] ring — fine for proportions. */
const ringArea = (ring) => {
    let area = 0;
    for (let i = 0; i < ring.length - 1; i++) {
        area += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    }
    return Math.abs(area / 2);
};

const closedHexRing = (cell) => {
    const ring = cellToBoundary(cell, true); // [lng, lat] pairs
    return [...ring, ring[0]];
};

test("single-kind bin emits one whole-hex feature with a closed ring", () => {
    const fc = buildEventFeatures([{ ...BERLIN, action: "login" }], 2);
    assert.equal(fc.features.length, 1);
    const [feature] = fc.features;
    assert.equal(feature.properties.action, "login");
    assert.equal(feature.properties.count, 1);
    const ring = feature.geometry.coordinates[0];
    assert.deepEqual(ring[0], ring[ring.length - 1], "ring must close");
    const boundary = cellToBoundary(feature.properties.cell);
    assert.equal(ring.length, boundary.length + 1);
});

test("multi-kind bin cuts wedges with area proportional to counts", () => {
    const points = [
        ...Array.from({ length: 3 }, () => ({ ...BERLIN, action: "login" })),
        { ...BERLIN, action: "login_failed" },
    ];
    const fc = buildEventFeatures(points, 2);
    assert.equal(fc.features.length, 2);
    const login = fc.features.find((f) => f.properties.action === "login");
    const failed = fc.features.find((f) => f.properties.action === "login_failed");
    const loginArea = ringArea(login.geometry.coordinates[0]);
    const failedArea = ringArea(failed.geometry.coordinates[0]);
    const ratio = loginArea / failedArea;
    assert.ok(ratio > 2.4 && ratio < 3.6, `expected ~3:1 area split, got ${ratio}`);
    const hexArea = ringArea(closedHexRing(login.properties.cell));
    const sum = loginArea + failedArea;
    assert.ok(Math.abs(sum - hexArea) / hexArea < 0.05, "wedges must tile the hex");
});

test("heights scale relative to the fullest bin with a 15% floor", () => {
    const points = [
        ...Array.from({ length: 10 }, () => ({ ...BERLIN, action: "login" })),
        { ...PRAGUE, action: "login" },
    ];
    const fc = buildEventFeatures(points, 2);
    const hMax = 1.5 * getHexagonEdgeLengthAvg(3, UNITS.m); // res 3 band at z2
    const berlin = fc.features.find((f) => f.properties.total === 10);
    const prague = fc.features.find((f) => f.properties.total === 1);
    assert.ok(Math.abs(berlin.properties.height - hMax) < 1);
    assert.ok(Math.abs(prague.properties.height - 0.15 * hMax) < 1);
});

test("wedges of one bin share the bin height", () => {
    const fc = buildEventFeatures(
        [
            { ...BERLIN, action: "login" },
            { ...BERLIN, action: "logout" },
        ],
        2,
    );
    assert.equal(fc.features.length, 2);
    const [a, b] = fc.features;
    assert.equal(a.properties.height, b.properties.height);
});

test("pointsInCell returns the points binned into a cell at the zoom band res", async () => {
    const { pointsInCell } = await import("../out/hexworld/wedges.js");
    const points = [
        { id: "a", ...BERLIN, action: "login" },
        { id: "b", ...BERLIN, action: "logout" },
        { id: "c", ...PRAGUE, action: "login" },
    ];
    const fc = buildEventFeatures(points, 2);
    const berlinCell = fc.features.find((f) => f.properties.total === 2).properties.cell;
    const hits = pointsInCell(points, 2, berlinCell);
    assert.deepEqual(hits.map((p) => p.id).sort(), ["a", "b"]);
    assert.deepEqual(pointsInCell(points, 2, "830000fffffffff"), []);
});

test("binAtLocation resolves a lat/lon to its cell and binned points", async () => {
    const { binAtLocation } = await import("../out/hexworld/wedges.js");
    const points = [
        { id: "a", ...BERLIN, action: "login" },
        { id: "b", ...BERLIN, action: "logout" },
        { id: "c", ...PRAGUE, action: "login" },
    ];
    // A click never lands exactly on the seeded coordinate; nearby must hit.
    const hit = binAtLocation(points, 4.2, 52.528, 13.423);
    assert.equal(
        hit.points
            .map((p) => p.id)
            .sort()
            .join(","),
        "a,b",
    );
    const fc = buildEventFeatures(points, 4.2);
    const berlinCell = fc.features.find((f) => f.properties.total === 2).properties.cell;
    assert.equal(hit.cell, berlinCell);
    const miss = binAtLocation(points, 4.2, 0, -30); // mid-Atlantic
    assert.equal(miss.points.length, 0);
});
