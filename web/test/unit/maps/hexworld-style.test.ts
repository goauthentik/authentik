import { layerById, layoutOf, paintOf, required } from "./helpers.js";

import type { BasemapTheme } from "#elements/maps/basemap-style";
import {
    bandFadeOpacity,
    buildHexworldStyle,
    HEXWORLD_ATTRIBUTION,
    wedgeColors,
} from "#elements/maps/hexworld-style";

import type { ExpressionSpecification, VectorSourceSpecification } from "maplibre-gl";
import { expect, test } from "vitest";

const style = buildHexworldStyle({ archiveURL: "/static/dist/assets/maps/hexworld.pmtiles" });

const hexworldSource = (spec = style) => spec.sources.hexworld as VectorSourceSpecification;

test("style uses the pmtiles protocol with promoted h3 ids", () => {
    const source = hexworldSource();
    expect(source.type).toBe("vector");
    expect(source.url).toBe("pmtiles:///static/dist/assets/maps/hexworld.pmtiles");
    expect(source.promoteId).toStrictEqual({ hex: "h3" });
    // The shipped archive carries hex/border geometry through z7 (the zoned
    // res-5 detail band). Declaring higher makes MapLibre fetch z8 tiles
    // that hold only labels; declaring lower wastes the detail band.
    expect(source.maxzoom).toBe(7);
    expect(source.attribution).toBe(HEXWORLD_ATTRIBUTION);
});

test("source maxzoom is overridable for a finer archive cut", () => {
    const r5 = buildHexworldStyle({ archiveURL: "/x.pmtiles", maxzoom: 8 });
    expect(hexworldSource(r5).maxzoom).toBe(8);
});

test("style has hex fill + label layers with name:en fallback", () => {
    const ids = style.layers.map((layer) => layer.id);
    expect(ids.includes("hexworld-background")).toBeTruthy();
    expect(ids.includes("hexworld-hex")).toBeTruthy();
    const labels = style.layers.filter((layer) => layer.type === "symbol");
    expect(labels.length >= 2, "expected kind-gated symbol layers").toBeTruthy();
    for (const layer of labels) {
        expect(layoutOf(layer)["text-field"]).toStrictEqual([
            "coalesce",
            ["get", "name:en"],
            ["get", "name"],
        ]);
    }
});

test("style has country + region border layers filtered by level", () => {
    const ids = style.layers.map((layer) => layer.id);
    const outlineIdx = ids.indexOf("hexworld-hex-outline");
    const regionIdx = ids.indexOf("hexworld-region-borders");
    const bordersIdx = ids.indexOf("hexworld-borders");
    expect(regionIdx, "expected a hexworld-region-borders layer").not.toBe(-1);
    expect(bordersIdx, "expected a hexworld-borders layer").not.toBe(-1);
    expect(regionIdx > outlineIdx, "region borders must render above hex outlines").toBeTruthy();
    expect(bordersIdx > regionIdx, "country borders must render above region borders").toBeTruthy();
    const region = required(style.layers[regionIdx], "region border layer");
    const country = required(style.layers[bordersIdx], "country border layer");
    expect("source-layer" in region && region["source-layer"]).toBe("borders");
    expect("source-layer" in country && country["source-layer"]).toBe("borders");
    expect("filter" in region && region.filter).toStrictEqual(["==", ["get", "level"], 1]);
    expect("filter" in country && country.filter).toStrictEqual(["==", ["get", "level"], 0]);
    // Region borders are gated to res-4-and-finer zooms so world view stays
    // readable — res 4 starts at z3 with the current bands.
    expect((region.minzoom ?? 0) >= 3).toBeTruthy();
});

test("airgap: default style references no absolute URLs", () => {
    const json = JSON.stringify(style);
    expect(!/https?:\/\//.test(json), "style must not reach external hosts").toBeTruthy();
});

test("dark theme swaps palette", () => {
    const dark = buildHexworldStyle({ archiveURL: "/x.pmtiles", theme: "dark" });
    const bg = (spec: typeof style) =>
        paintOf(layerById(spec, "hexworld-background"))["background-color"];
    expect(bg(dark)).not.toBe(bg(style));
});

test("wedge palette covers the five event actions in both themes", () => {
    // "11184809" is EventActions.UnknownDefaultOpenApi — drf-spectacular's
    // sentinel for values outside the enum.
    const actions = ["login", "login_failed", "logout", "authorize_application", "11184809"];
    for (const theme of ["light", "dark"] satisfies BasemapTheme[]) {
        const colors: Record<string, string | undefined> = wedgeColors(theme);
        for (const action of actions) {
            expect(required(colors[action], action), `${theme}/${action}`).toMatch(
                /^#[0-9a-f]{6}$/i,
            );
        }
    }
});

test("bandFadeOpacity cross-fades bands at their boundaries", () => {
    const expr = bandFadeOpacity(0.95);
    expect(expr[0]).toBe("interpolate");
    expect(expr[2]).toStrictEqual(["zoom"]);
    // Stops come in [zoom, matchExpression] pairs from index 3 on.
    const stops: [number, ExpressionSpecification][] = [];
    for (let i = 3; i < expr.length; i += 2) {
        stops.push([expr[i] as number, expr[i + 1] as ExpressionSpecification]);
    }
    const valueFor = (match: ExpressionSpecification, res: number): unknown => {
        // ["match", ["get","res"], r1, v1, r2, v2, ..., fallback]
        for (let i = 2; i < match.length - 1; i += 2) {
            if (match[i] === res) return match[i + 1];
        }
        return match[match.length - 1];
    };
    const atZoom = (z: number) =>
        required(
            stops.find(([stop]) => stop === z),
            `stop at z${z}`,
        )[1];
    // z3: res-3 grid still fully present, res-4 not yet visible.
    expect(valueFor(atZoom(3), 3)).toBe(0.95);
    expect(valueFor(atZoom(3), 4)).toBe(0);
    // End of the first fade window: grids have swapped.
    expect(valueFor(atZoom(3.9), 3)).toBe(0);
    expect(valueFor(atZoom(3.9), 4)).toBe(0.95);
    // z7: the res-5 overlay starts invisible and fades in over the res-4 base,
    // which never fades out (it backs the overlay outside the detail zone).
    expect(valueFor(atZoom(7), 5)).toBe(0);
    expect(valueFor(atZoom(7), 4)).toBe(0.95);
    expect(valueFor(atZoom(7.9), 5)).toBe(0.95);
    expect(valueFor(atZoom(7.9), 4)).toBe(0.95);
    // Old archives without a res property keep the base opacity.
    expect(valueFor(atZoom(3), 99)).toBe(0.95);
});

test("hex and border layers use the band fade", () => {
    const faded = buildHexworldStyle({ archiveURL: "/x.pmtiles" });
    const opacity = (id: string, property: string) =>
        (paintOf(layerById(faded, id))[property] as unknown[])[0];
    expect(opacity("hexworld-hex", "fill-opacity")).toBe("interpolate");
    expect(opacity("hexworld-hex-outline", "line-opacity")).toBe("interpolate");
    expect(opacity("hexworld-borders", "line-opacity")).toBe("interpolate");
    expect(opacity("hexworld-region-borders", "line-opacity")).toBe("interpolate");
});

test("label layers sort collisions by population and regions start at z3", () => {
    const spec = buildHexworldStyle({ archiveURL: "/x.pmtiles" });
    expect(layerById(spec, "hexworld-label-region").minzoom).toBe(3);
    for (const kind of ["country", "region", "locality"]) {
        const sort = layoutOf(layerById(spec, `hexworld-label-${kind}`))["symbol-sort-key"];
        expect(Array.isArray(sort), `${kind} needs a symbol-sort-key`).toBeTruthy();
    }
});
