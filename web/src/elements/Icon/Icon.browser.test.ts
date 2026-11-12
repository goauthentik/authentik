import "#elements/ak-icon";
import type { Icon } from "#elements/ak-icon";

import { afterEach, describe, expect, it } from "vitest";
import { page } from "vitest/browser";

import { html, render, type TemplateResult } from "lit";

const mounted = new Set<HTMLElement>();

async function mount(template: TemplateResult): Promise<Icon> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);
    render(template, container);

    const element = container.querySelector("ak-icon")!;
    await element.updateComplete;

    return element;
}

const image = (element: Icon) => element.style.getPropertyValue("--ak-icon--image");

describe("ak-icon", () => {
    afterEach(() => {
        mounted.forEach((container) => container.remove());
        mounted.clear();
    });

    it("maps a dotted token to its catalog property", async () => {
        const element = await mount(html`<ak-icon name="status.success"></ak-icon>`);
        expect(image(element)).toBe("var(--ak-icon--status-success)");
    });

    it("clears the image when the name becomes invalid", async () => {
        const element = await mount(html`<ak-icon name="status.success"></ak-icon>`);
        element.name = "status success; color: red";
        await element.updateComplete;
        expect(image(element)).toBe("");
    });

    it("is hidden from assistive technology without a label", async () => {
        await mount(html`<ak-icon name="status.success"></ak-icon>`);
        expect(page.getByRole("img").elements()).toHaveLength(0);
    });

    it("is an image named by its label", async () => {
        const element = await mount(html`<ak-icon name="status.success"></ak-icon>`);
        element.label = "Success";
        await element.updateComplete;
        await expect.element(page.getByRole("img", { name: "Success" })).toBeInTheDocument();
    });

    it("sizes itself to the surrounding font", async () => {
        const element = await mount(
            html`<span style="font-size: 32px"><ak-icon name="status.success"></ak-icon></span>`,
        );

        expect(element.getBoundingClientRect().width).toBe(32);
    });
});
