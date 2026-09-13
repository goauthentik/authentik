import { required } from "./helpers.js";

import { binAtLocation, binEvents, buildEventFeatures, pointsInCell } from "#elements/maps/wedges";

import { cellToBoundary, getHexagonEdgeLengthAvg, UNITS } from "h3-js";
import { expect, test } from "vitest";

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
    expect(bins.size).toBe(2);
    const berlin = required(
        [...bins.values()].find((bin) => bin.total === 4),
        "4-event bin for Berlin",
    );
    expect(berlin.counts.get("login")).toBe(2);
    expect(berlin.counts.get("login_failed")).toBe(1);
    expect(berlin.counts.get("other")).toBe(1);
});

test("binEvents uses the zoom band resolution (coarser bins at world zoom)", () => {
    const close = [
        { lat: 52.52, lon: 13.405, action: "login" },
        { lat: 52.6, lon: 13.6, action: "login" },
    ];
    const world = binEvents(close, 0); // res 3
    const regional = binEvents(close, 8); // res 5
    expect(world.size).toBe(1);
    expect(regional.size).toBe(2);
});

/** Planar shoelace area on a closed [lng, lat] ring — fine for proportions. */
const ringArea = (ring: number[][]) => {
    let area = 0;
    for (let i = 0; i < ring.length - 1; i++) {
        area += ring[i]![0]! * ring[i + 1]![1]! - ring[i + 1]![0]! * ring[i]![1]!;
    }
    return Math.abs(area / 2);
};

const closedHexRing = (cell: string) => {
    const ring = cellToBoundary(cell, true); // [lng, lat] pairs
    return [...ring, ring[0]!];
};

test("single-kind bin emits one whole-hex feature with a closed ring", () => {
    const fc = buildEventFeatures([{ ...BERLIN, action: "login" }], 2);
    expect(fc.features.length).toBe(1);
    const feature = required(fc.features[0], "wedge feature");
    expect(feature.properties.action).toBe("login");
    expect(feature.properties.count).toBe(1);
    const ring = required(feature.geometry.coordinates[0], "outer ring");
    expect(ring[0], "ring must close").toStrictEqual(ring[ring.length - 1]);
    const boundary = cellToBoundary(feature.properties.cell);
    expect(ring.length).toBe(boundary.length + 1);
});

test("multi-kind bin cuts wedges with area proportional to counts", () => {
    const points = [
        ...Array.from({ length: 3 }, () => ({ ...BERLIN, action: "login" })),
        { ...BERLIN, action: "login_failed" },
    ];
    const fc = buildEventFeatures(points, 2);
    expect(fc.features.length).toBe(2);
    const login = required(
        fc.features.find((f) => f.properties.action === "login"),
        "login wedge",
    );
    const failed = required(
        fc.features.find((f) => f.properties.action === "login_failed"),
        "login_failed wedge",
    );
    const loginArea = ringArea(required(login.geometry.coordinates[0], "login ring"));
    const failedArea = ringArea(required(failed.geometry.coordinates[0], "failed ring"));
    const ratio = loginArea / failedArea;
    expect(ratio > 2.4 && ratio < 3.6, `expected ~3:1 area split, got ${ratio}`).toBeTruthy();
    const hexArea = ringArea(closedHexRing(login.properties.cell));
    const sum = loginArea + failedArea;
    expect(Math.abs(sum - hexArea) / hexArea < 0.05, "wedges must tile the hex").toBeTruthy();
});

test("heights scale relative to the fullest bin with a 15% floor", () => {
    const points = [
        ...Array.from({ length: 10 }, () => ({ ...BERLIN, action: "login" })),
        { ...PRAGUE, action: "login" },
    ];
    const fc = buildEventFeatures(points, 2);
    const hMax = 1.5 * getHexagonEdgeLengthAvg(3, UNITS.m); // res 3 band at z2
    const berlin = required(
        fc.features.find((f) => f.properties.total === 10),
        "Berlin column",
    );
    const prague = required(
        fc.features.find((f) => f.properties.total === 1),
        "Prague column",
    );
    expect(Math.abs(berlin.properties.height - hMax) < 1).toBeTruthy();
    expect(Math.abs(prague.properties.height - 0.15 * hMax) < 1).toBeTruthy();
});

test("wedges of one bin share the bin height", () => {
    const fc = buildEventFeatures(
        [
            { ...BERLIN, action: "login" },
            { ...BERLIN, action: "logout" },
        ],
        2,
    );
    expect(fc.features.length).toBe(2);
    const a = required(fc.features[0], "first wedge");
    const b = required(fc.features[1], "second wedge");
    expect(a.properties.height).toBe(b.properties.height);
});

test("pointsInCell returns the points binned into a cell at the zoom band res", () => {
    const points = [
        { id: "a", ...BERLIN, action: "login" },
        { id: "b", ...BERLIN, action: "logout" },
        { id: "c", ...PRAGUE, action: "login" },
    ];
    const fc = buildEventFeatures(points, 2);
    const berlinCell = required(
        fc.features.find((f) => f.properties.total === 2),
        "Berlin column",
    ).properties.cell;
    const hits = pointsInCell(points, 2, berlinCell);
    expect(hits.map((p) => p.id).sort()).toStrictEqual(["a", "b"]);
    expect(pointsInCell(points, 2, "830000fffffffff")).toStrictEqual([]);
});

test("binAtLocation resolves a lat/lon to its cell and binned points", () => {
    const points = [
        { id: "a", ...BERLIN, action: "login" },
        { id: "b", ...BERLIN, action: "logout" },
        { id: "c", ...PRAGUE, action: "login" },
    ];
    // A click never lands exactly on the seeded coordinate; nearby must hit.
    const hit = binAtLocation(points, 4.2, 52.528, 13.423);
    expect(
        hit.points
            .map((p) => p.id)
            .sort()
            .join(","),
    ).toBe("a,b");
    const fc = buildEventFeatures(points, 4.2);
    const berlinCell = required(
        fc.features.find((f) => f.properties.total === 2),
        "Berlin column",
    ).properties.cell;
    expect(hit.cell).toBe(berlinCell);
    const miss = binAtLocation(points, 4.2, 0, -30); // mid-Atlantic
    expect(miss.points.length).toBe(0);
});
