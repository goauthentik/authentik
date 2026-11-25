import "#elements/Label";
import { akLabel, type Label } from "#elements/Label";

import { afterEach, describe, expect, it, vi } from "vitest";

import { html, render } from "lit";

// The minimal tokens needed to support testing
const tokens = [
    "--ak-c-label--m-outline--BackgroundColor: rgb(1, 2, 3)",
    "--ak-c-label--m-red--BackgroundColor: rgb(200, 0, 0)",
].join(";");

const OUTLINE = "rgb(1, 2, 3)";
const FILLED = "rgb(200, 0, 0)";

async function mount(template: unknown): Promise<Label> {
    const host = document.createElement("div");
    host.setAttribute("style", tokens);
    document.body.append(host);
    render(template, host);

    const label = host.querySelector("ak-label")!;
    await label.updateComplete;

    return label;
}

const part = (label: Label, name: string) =>
    label.shadowRoot!.querySelector<HTMLElement>(`[part="${name}"]`)!;

const iconClasses = (label: Label) =>
    [...(part(label, "icon").querySelector("i")?.classList ?? [])].sort();

const background = (label: Label) => getComputedStyle(part(label, "label")).backgroundColor;

afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
});

describe("ak-label content", () => {
    it("renders slotted text in the text part", async () => {
        const label = await mount(html`<ak-label>Hello</ak-label>`);
        const slot = part(label, "text").querySelector("slot")!;

        expect(slot.assignedNodes().map((n) => n.textContent)).toEqual(["Hello"]);
    });

    it("lets the `label` state replace the default slot", async () => {
        const label = await mount(html`<ak-label>Slotted</ak-label>`);
        label.label = "Override";
        await label.updateComplete;

        expect(part(label, "text").textContent).toBe("Override");
        expect(part(label, "text").querySelector("slot")).toBeNull();
    });
});

describe("ak-label status", () => {
    it.each([
        ["danger", "status-red", "fa-times"],
        ["error", "status-red", "fa-times"],
        ["warning", "status-orange", "fa-exclamation-triangle"],
        ["bad", "status-orange", "fa-exclamation-triangle"],
        ["success", "status-green", "fa-check"],
        ["good", "status-green", "fa-check"],
        ["ok", "status-green", "fa-check"],
        ["running", "status-blue", "fa-clock"],
        ["info", "status-gray", "fa-info-circle"],
        ["neutral", "status-gray", "fa-times"],
        ["unknown", "status-gray", "fa-question"],
    ])("maps %s to %s with %s", async (status, color, icon) => {
        const label = await mount(html`<ak-label status=${status}>x</ak-label>`);

        expect(part(label, "label").classList.contains(color)).toBe(true);
        expect(iconClasses(label)).toEqual(["fa-fw", "fas", icon].sort());
        expect(part(label, "icon").classList.contains("has-content")).toBe(true);
    });

    it("hides the status icon from assistive technology", async () => {
        const label = await mount(html`<ak-label status="success">x</ak-label>`);

        expect(part(label, "icon").querySelector("i")!.getAttribute("aria-hidden")).toBe("true");
    });

    it("warns on an unrecognized status and applies no color", async () => {
        const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
        const label = await mount(html`<ak-label status="bogus">x</ak-label>`);

        expect(warn).toHaveBeenCalledWith(expect.stringContaining("'bogus'"));

        expect([...part(label, "label").classList].some((c) => c.startsWith("status-"))).toBe(
            false,
        );

        expect(part(label, "icon").querySelector("i")).toBeNull();
    });
});

describe("ak-label icon", () => {
    it("renders no icon chrome by default", async () => {
        const label = await mount(html`<ak-label>x</ak-label>`);

        expect(part(label, "icon").classList.contains("has-content")).toBe(false);
        expect(part(label, "icon").querySelector("i")).toBeNull();
    });

    it("renders an explicit icon", async () => {
        const label = await mount(html`<ak-label icon="fa-star">x</ak-label>`);

        expect(iconClasses(label)).toEqual(["fa-fw", "fa-star", "fas"]);
        expect(part(label, "icon").classList.contains("has-content")).toBe(true);
    });

    it("prefers an explicit icon over the status icon, keeping the status color", async () => {
        const label = await mount(html`<ak-label status="danger" icon="fa-star">x</ak-label>`);

        expect(iconClasses(label)).toEqual(["fa-fw", "fa-star", "fas"]);
        expect(part(label, "label").classList.contains("status-red")).toBe(true);
    });

    it("marks the icon part when an element is slotted into it", async () => {
        const label = await mount(html`<ak-label><span slot="icon">★</span>x</ak-label>`);
        // slotchange fires asynchronously after first render.
        await new Promise((r) => setTimeout(r));
        await label.updateComplete;

        expect(part(label, "icon").classList.contains("has-content")).toBe(true);
    });
});

describe("ak-label outline", () => {
    it("fills with the status color without outline", async () => {
        expect(background(await mount(html`<ak-label status="danger">x</ak-label>`))).toBe(FILLED);
    });

    it("fills with the color attribute without outline", async () => {
        expect(background(await mount(html`<ak-label color="red">x</ak-label>`))).toBe(FILLED);
    });

    it("outlines a color label", async () => {
        expect(background(await mount(html`<ak-label color="red" outline>x</ak-label>`))).toBe(
            OUTLINE,
        );
    });

    it("outlines a status label", async () => {
        expect(background(await mount(html`<ak-label status="danger" outline>x</ak-label>`))).toBe(
            OUTLINE,
        );
    });
});

describe("akLabel()", () => {
    it("wraps string content in a span", async () => {
        const label = await mount(akLabel({}, "Hi"));
        const span = label.querySelector("span")!;

        expect(span.textContent).toBe("Hi");
    });

    it("spreads properties onto the element as attributes", async () => {
        const label = await mount(
            akLabel({ color: "red", icon: "fa-star", status: "danger", outline: true }, "x"),
        );

        expect(label.getAttribute("color")).toBe("red");
        expect(label.icon).toBe("fa-star");
        expect(label.status).toBe("danger");
        expect(label.hasAttribute("outline")).toBe(true);
    });

    it("omits boolean attributes when false", async () => {
        const label = await mount(akLabel({ color: "red", outline: false, compact: false }, "x"));

        expect(label.hasAttribute("outline")).toBe(false);
        expect(label.hasAttribute("compact")).toBe(false);
        expect(background(label)).toBe(FILLED);
    });

    it("sets boolean attributes empty when true", async () => {
        const label = await mount(akLabel({ outline: true, compact: true }, "x"));

        expect(label.getAttribute("outline")).toBe("");
        expect(label.getAttribute("compact")).toBe("");
    });
});
