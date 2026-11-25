import "#elements/ak-spinner";
import { akSpinner, type Spinner } from "#elements/ak-spinner";

import { afterEach, describe, expect, it } from "vitest";

import { html, render, type TemplateResult } from "lit";

const mounted = new Set<HTMLElement>();

// Fixed diameters, so size assertions don't depend on the global stylesheet being loaded.
const TOKENS = [
    "--pf-c-spinner--m-sm--diameter: 10px",
    "--pf-c-spinner--m-md--diameter: 20px",
    "--pf-c-spinner--m-lg--diameter: 30px",
    "--pf-c-spinner--m-xl--diameter: 40px",
    "--pf-c-spinner--m-inline--diameter: 1em",
    "font-size: 16px",
].join(";");

async function mount(template: TemplateResult): Promise<Spinner> {
    const container = document.body.appendChild(document.createElement("div"));
    container.setAttribute("style", TOKENS);
    mounted.add(container);
    render(template, container);

    const element = container.querySelector("ak-spinner")!;
    await element.updateComplete;

    return element;
}

const part = (element: Spinner, name: string) =>
    element.renderRoot.querySelector<HTMLElement>(`[part="${name}"]`);

const width = (element: Spinner) => element.getBoundingClientRect().width;

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-spinner: structure", () => {
    it("renders the spinner wrapper and its three animated parts", async () => {
        const element = await mount(html`<ak-spinner></ak-spinner>`);

        for (const name of ["spinner", "clipper", "leading-ball", "trailing-ball"]) {
            expect(part(element, name), name).not.toBeNull();
        }

        expect(part(element, "spinner")!.contains(part(element, "clipper"))).toBe(true);
    });

    it("animates the wrapper", async () => {
        const element = await mount(html`<ak-spinner></ak-spinner>`);

        expect(getComputedStyle(part(element, "spinner")!).animationName).toBe(
            "pf-animation-spinner-parent",
        );
    });
});

describe("ak-spinner: accessibility", () => {
    it("defaults to a progressbar with a loading value text", async () => {
        const element = await mount(html`<ak-spinner></ak-spinner>`);

        expect(element.getAttribute("role")).toBe("progressbar");
        expect(element.getAttribute("aria-valuetext")).toBe("Loading...");
    });

    it("keeps a role and value text the consumer supplies", async () => {
        const element = await mount(
            html`<ak-spinner role="status" aria-valuetext="Syncing"></ak-spinner>`,
        );

        expect(element.getAttribute("role")).toBe("status");
        expect(element.getAttribute("aria-valuetext")).toBe("Syncing");
    });
});

describe("ak-spinner: size", () => {
    it("defaults to md and reflects it", async () => {
        const element = await mount(html`<ak-spinner></ak-spinner>`);

        expect(element.size).toBe("md");
        expect(element.getAttribute("size")).toBe("md");
    });

    it.each([
        ["sm", 10],
        ["md", 20],
        ["lg", 30],
        ["xl", 40],
    ] as const)("sizes the host to the %s diameter", async (size, expected) => {
        const element = await mount(html`<ak-spinner size=${size}></ak-spinner>`);

        expect(width(element)).toBe(expected);
        expect(element.getBoundingClientRect().height).toBe(expected);
    });

    it("resizes when the size property changes", async () => {
        const element = await mount(html`<ak-spinner size="sm"></ak-spinner>`);

        element.size = "xl";
        await element.updateComplete;

        expect(element.getAttribute("size")).toBe("xl");
        expect(width(element)).toBe(40);
    });

    it("sizes to the surrounding text when inline", async () => {
        const element = await mount(html`<ak-spinner inline></ak-spinner>`);

        expect(width(element)).toBe(16);
    });
});

describe("akSpinner builder", () => {
    it("passes size through as an attribute", async () => {
        const element = await mount(akSpinner({ size: "lg" }));

        expect(element.getAttribute("size")).toBe("lg");
        expect(width(element)).toBe(30);
    });

    it("leaves the default size to the element", async () => {
        const element = await mount(akSpinner());

        expect(element.size).toBe("md");
    });

    it("spreads the remaining props onto the host", async () => {
        const element = await mount(akSpinner({ "id": "busy", "aria-label": "Saving" }));

        expect(element.id).toBe("busy");
        expect(element.getAttribute("aria-label")).toBe("Saving");
    });

    it("adds no stray attributes", async () => {
        const element = await mount(akSpinner({ size: "sm" }));

        expect(element.getAttributeNames().sort()).toEqual(
            ["aria-valuetext", "role", "size"].sort(),
        );
    });
});
