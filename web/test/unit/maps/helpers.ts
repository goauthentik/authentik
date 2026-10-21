import type { LayerSpecification, StyleSpecification } from "maplibre-gl";
import { expect } from "vitest";

/**
 * Narrow away the `null | undefined` that lookups (`find`, `Map.get`, a
 * parser that rejects bad input) carry, failing the test if it is actually
 * absent. Keeps assertions readable instead of scattering `!` through them.
 */
export function required<T>(value: T | null | undefined, what = "value"): T {
    if (value === null || value === undefined) {
        expect.unreachable(`expected ${what} to be present`);
    }

    return value;
}

/** The style layer with this id, or a test failure naming the missing id. */
export function layerById(style: StyleSpecification, id: string): LayerSpecification {
    return required(
        style.layers.find((layer) => layer.id === id),
        `layer ${id}`,
    );
}

/**
 * `paint` and `layout` are per-layer-type unions in MapLibre's typings, so a
 * property only reachable on one variant cannot be indexed off the union.
 * Tests assert on individual properties by name; widen once, here, rather than
 * narrowing by layer type at every call site.
 */
export function paintOf(layer: LayerSpecification): Record<string, unknown> {
    return required(layer.paint, `paint on layer ${layer.id}`) as Record<string, unknown>;
}

export function layoutOf(layer: LayerSpecification): Record<string, unknown> {
    return required(layer.layout, `layout on layer ${layer.id}`) as Record<string, unknown>;
}
