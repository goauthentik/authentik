// Side-effect import: the module registers <ak-map>. Kept separate from the
// type import so it cannot be elided as type-only.
import "#elements/maps/ak-map";

import type { AKMap } from "#elements/maps/ak-map";

import { afterEach, expect, test } from "vitest";

const mounted: HTMLElement[] = [];

function container(): HTMLElement {
    const element = document.createElement("div");

    // MapLibre reads the container's size on construction; a zero-height box
    // makes it skip the initial render and never fire `load`.
    element.style.width = "480px";
    element.style.height = "320px";
    document.body.append(element);
    mounted.push(element);

    return element;
}

afterEach(() => {
    for (const element of mounted.splice(0)) element.remove();
});

async function mount(parent: HTMLElement): Promise<AKMap> {
    // Guards the whole file: an elided side-effect import leaves createElement
    // returning a plain HTMLElement, and every assertion below reads undefined.
    expect(customElements.get("ak-map"), "<ak-map> must be registered").toBeDefined();

    const map = document.createElement("ak-map");
    parent.append(map);
    await map.updateComplete;

    return map;
}

/** The live MapLibre instance, which `ak-map` keeps `protected`. */
const instanceOf = (map: AKMap): unknown => (map as unknown as { map: unknown }).map;

test("builds a MapLibre instance once connected", async () => {
    const map = await mount(container());

    expect(instanceOf(map)).toBeTruthy();
});

test("tears the map down on disconnect", async () => {
    const map = await mount(container());
    map.remove();

    expect(instanceOf(map)).toBeNull();
});

test("rebuilds the map when re-parented", async () => {
    const first = container();
    const second = container();
    const map = await mount(first);
    const original = instanceOf(map);

    // Moving a custom element runs disconnectedCallback then
    // connectedCallback. firstUpdated() has already fired and never fires
    // again, so re-creating the map has to hang off connectedCallback —
    // otherwise the element comes back permanently blank.
    second.append(map);
    await map.updateComplete;

    const rebuilt = instanceOf(map);
    expect(rebuilt).not.toBeNull();
    expect(rebuilt).not.toBe(original);
    expect(map.parentElement).toBe(second);
});
