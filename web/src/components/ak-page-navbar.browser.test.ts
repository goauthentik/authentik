import "#components/ak-page-navbar";
import { DefaultBrand } from "#common/ui/config";

import { AKPageNavbar } from "#components/ak-page-navbar";

import { CurrentBrand } from "@goauthentik/api";

import { afterEach, describe, expect, it } from "vitest";
import { page } from "vitest/browser";

/**
 * The navbar with a fixed brand, which the interface normally provides through context.
 */
class TestPageNavbar extends AKPageNavbar {
    brand: CurrentBrand = DefaultBrand;
}

customElements.define("ak-test-page-navbar", TestPageNavbar);

declare global {
    interface HTMLElementTagNameMap {
        "ak-test-page-navbar": TestPageNavbar;
    }
}

const mounted: HTMLElement[] = [];

afterEach(async () => {
    for (const element of mounted.splice(0)) {
        element.remove();
    }

    await page.viewport(1280, 800);
});

async function mountNavbar(header: string): Promise<AKPageNavbar> {
    const navbar = document.createElement("ak-test-page-navbar");
    navbar.header = header;

    document.body.append(navbar);
    mounted.push(navbar);

    await navbar.updateComplete;

    return navbar;
}

function userInterfaceLink(navbar: AKPageNavbar) {
    return navbar.shadowRoot!.querySelector<HTMLAnchorElement>("a[href$='if/user/']")!;
}

describe("ak-page-navbar", () => {
    it("shows the user interface link on a wide viewport", async () => {
        await page.viewport(1280, 800);

        const navbar = await mountNavbar("Outposts");

        expect(getComputedStyle(userInterfaceLink(navbar)).display).not.toBe("none");
    });

    it("hides the user interface link on a narrow viewport", async () => {
        await page.viewport(375, 812);

        const navbar = await mountNavbar("Outposts");

        expect(getComputedStyle(userInterfaceLink(navbar)).display).toBe("none");
    });

    it("uses one column per area on a narrow viewport", async () => {
        await page.viewport(375, 812);

        const navbar = await mountNavbar("Outposts");
        const content = navbar.shadowRoot!.querySelector<HTMLElement>(".main-content")!;
        const columns = getComputedStyle(content).gridTemplateColumns.match(/[\d.]+px/g);

        // Toggle, title and buttons. A leftover fourth column puts the buttons
        // in the flexible column, which then can't shrink below their width.
        expect(columns).toHaveLength(3);
    });
});
