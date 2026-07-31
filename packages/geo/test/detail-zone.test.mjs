import assert from "node:assert/strict";
import { test } from "node:test";

import {
    computeDetailZone,
    detailCellsForRes5,
    isDetailCell,
} from "../out/hexworld/detail-zone.js";

import { cellToChildren, latLngToCell } from "h3-js";

const locality = (name, lng, lat, population = 100_000) => ({
    kind: "locality",
    name,
    nameEn: name,
    lng,
    lat,
    minZoom: 4,
    population,
});

test("computeDetailZone with ring=0 gives one res-4 cell per label", () => {
    const label = locality("A", 0, 0);
    const zone = computeDetailZone([label], { ring: 0, minPop: 0 });
    assert.equal(zone.seedCount, 1);
    assert.equal(zone.baseCells.size, 1);
    assert.ok(zone.baseCells.has(latLngToCell(0, 0, 4)));
    // Res-5 children of one res-4 cell = 7.
    assert.equal(zone.detailCells.size, 7);
});

test("computeDetailZone with ring=1 expands to 7 res-4 cells around each seed", () => {
    const label = locality("A", 0, 0);
    const zone = computeDetailZone([label], { ring: 1, minPop: 0 });
    assert.equal(zone.baseCells.size, 7);
    // 7 res-4 cells × 7 res-5 children = 49.
    assert.equal(zone.detailCells.size, 49);
});

test("computeDetailZone filters below minPop", () => {
    const small = locality("small", 0, 0, 100);
    const big = locality("big", 20, 20, 1_000_000);
    const zone = computeDetailZone([small, big], { ring: 0, minPop: 50_000 });
    assert.equal(zone.seedCount, 1);
    assert.equal(zone.baseCells.size, 1);
});

test("computeDetailZone unions overlapping rings without doubling", () => {
    // Two labels one res-4 cell apart. Their rings share ~4 cells.
    const label1 = locality("A", 0, 0);
    const label2 = locality("B", 1, 1);
    const zone = computeDetailZone([label1, label2], { ring: 1, minPop: 0 });
    // At most 14 res-4 cells; expect fewer if the disks overlap.
    assert.ok(zone.baseCells.size <= 14);
    // res-5 children = 7 × base.
    assert.equal(zone.detailCells.size, zone.baseCells.size * 7);
});

test("computeDetailZone ignores non-localities", () => {
    const country = { ...locality("US", 0, 0), kind: "country" };
    const region = { ...locality("CA", 0, 0), kind: "region" };
    const zone = computeDetailZone([country, region], { ring: 0, minPop: 0 });
    assert.equal(zone.seedCount, 0);
    assert.equal(zone.baseCells.size, 0);
});

test("detailCellsForRes5 filters to cells inside the zone only", () => {
    const zone = computeDetailZone([locality("A", 0, 0)], { ring: 0, minPop: 0 });
    const inside = [...zone.detailCells];
    const outsideParent = latLngToCell(50, 50, 4);
    const outside = [...cellToChildren(outsideParent, 5)];
    const filtered = detailCellsForRes5([...inside, ...outside], zone);
    assert.equal(filtered.size, inside.length);
});

test("isDetailCell checks membership via the res-4 parent", () => {
    const zone = computeDetailZone([locality("A", 0, 0)], { ring: 0, minPop: 0 });
    const insideCell = [...zone.detailCells][0];
    assert.ok(isDetailCell(insideCell, zone));
    const outsideCell = cellToChildren(latLngToCell(50, 50, 4), 5)[0];
    assert.equal(isDetailCell(outsideCell, zone), false);
});
