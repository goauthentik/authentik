import "#elements/Tabs";
import type { Tabs } from "#elements/Tabs";

import { afterEach, describe, expect, it } from "vitest";
import { page } from "vitest/browser";

const mounted: HTMLElement[] = [];

afterEach(async () => {
    for (const element of mounted.splice(0)) {
        element.remove();
    }

    await page.viewport(1280, 800);
});

async function mountVerticalTabs(): Promise<Tabs> {
    const tabs = document.createElement("ak-tabs");
    // Set as an attribute, like the templates do, so the `:host([vertical])` styles apply.
    tabs.setAttribute("vertical", "");

    tabs.innerHTML = `
        <div role="tabpanel" slot="page-first" aria-label="First">First</div>
        <div role="tabpanel" slot="page-second" aria-label="Second">Second</div>
    `;

    document.body.append(tabs);
    mounted.push(tabs);

    await tabs.updateComplete;

    return tabs;
}

function tabList(tabs: Tabs) {
    return tabs.shadowRoot!.querySelector<HTMLElement>("[role='tablist']")!;
}

describe("ak-tabs vertical", () => {
    it("lays tabs out in a column beside the panel on a wide viewport", async () => {
        await page.viewport(1280, 800);

        const tabs = await mountVerticalTabs();

        expect(tabList(tabs).getAttribute("aria-orientation")).toBe("vertical");
        expect(getComputedStyle(tabs).display).toBe("grid");
    });

    it("lays tabs out in a row above the panel on a narrow viewport", async () => {
        await page.viewport(375, 812);

        const tabs = await mountVerticalTabs();

        expect(tabList(tabs).getAttribute("aria-orientation")).toBe("horizontal");
        expect(getComputedStyle(tabs).display).not.toBe("grid");
    });

    it("switches when the viewport is resized", async () => {
        await page.viewport(1280, 800);

        const tabs = await mountVerticalTabs();

        await page.viewport(375, 812);

        await expect.poll(() => tabList(tabs).getAttribute("aria-orientation")).toBe("horizontal");

        await page.viewport(1280, 800);

        await expect.poll(() => tabList(tabs).getAttribute("aria-orientation")).toBe("vertical");
    });
});
