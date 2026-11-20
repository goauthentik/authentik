// Side-effect import: the module registers <ak-mdx>. Kept separate from the
// type import so it cannot be elided as type-only.
import "#elements/ak-mdx/ak-mdx";

import type { AKMDX } from "#elements/ak-mdx/ak-mdx";

import { afterEach, expect, test } from "vitest";

const probeGlobal = globalThis as typeof globalThis & {
    __akMDXProbe?: () => string;
};

const mounted: HTMLElement[] = [];

afterEach(() => {
    delete probeGlobal.__akMDXProbe;

    for (const element of mounted.splice(0)) element.remove();
});

function mount(content: string): AKMDX {
    expect(customElements.get("ak-mdx"), "<ak-mdx> must be registered").toBeDefined();

    const element = document.createElement("ak-mdx");
    element.content = content;
    document.body.append(element);
    mounted.push(element);

    return element;
}

const renderedText = (element: AKMDX) => element.shadowRoot?.textContent ?? "";

test("does not evaluate expressions in API-supplied content", async () => {
    const calls: string[] = [];

    probeGlobal.__akMDXProbe = () => {
        calls.push("expression");

        return "EVALUATED";
    };

    const element = mount("Before {globalThis.__akMDXProbe()} after");

    await expect.poll(() => renderedText(element)).toContain("after");

    expect(calls, "the expression must not run").toEqual([]);
    expect(renderedText(element)).not.toContain("EVALUATED");
    expect(renderedText(element)).toContain("{globalThis.__akMDXProbe()}");
});

test("does not evaluate ESM exports in API-supplied content", async () => {
    const calls: string[] = [];

    probeGlobal.__akMDXProbe = () => {
        calls.push("export");

        return "EVALUATED";
    };

    const element = mount("export const probe = globalThis.__akMDXProbe()\n\nAfter the export.");

    await expect.poll(() => renderedText(element)).toContain("After the export.");

    expect(calls, "the export must not run").toEqual([]);
});

test("still renders Markdown in API-supplied content", async () => {
    const element = mount("Some **bold** text.");

    await expect.poll(() => element.shadowRoot?.querySelector("strong")?.textContent).toBe("bold");
});
