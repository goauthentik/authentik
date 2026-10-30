import { renderSourceIcon } from "#elements/sources/utils";

import type { ThemedUrls } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

import { render } from "lit";

const themedUrls: ThemedUrls = {
    light: "/static/authentik/sources/github/light.svg",
    dark: "/static/authentik/sources/github/dark.svg",
};

function renderIcon(...args: Parameters<typeof renderSourceIcon>): Element {
    const container = document.createElement("div");
    render(renderSourceIcon(...args), container);

    return container.firstElementChild!;
}

describe("renderSourceIcon", () => {
    it("renders the dark variant in the dark theme", () => {
        const icon = renderIcon("GitHub", themedUrls.light, themedUrls, "dark");

        expect(icon.getAttribute("src")).toBe(themedUrls.dark);
    });

    it("renders the light variant in the light theme", () => {
        const icon = renderIcon("GitHub", themedUrls.dark, themedUrls, "light");

        expect(icon.getAttribute("src")).toBe(themedUrls.light);
    });

    it("renders the icon URL in either theme when there are no themed URLs", () => {
        const icon = renderIcon("Custom", "/custom.png", null, "dark");

        expect(icon.getAttribute("src")).toBe("/custom.png");
    });

    it("renders the icon URL when the themed URLs lack the active theme", () => {
        const icon = renderIcon("Custom", "/custom.png", { light: "/custom-light.png" }, "dark");

        expect(icon.getAttribute("src")).toBe("/custom.png");
    });

    it("exposes the image as the source-icon part", () => {
        const icon = renderIcon("GitHub", themedUrls.light, themedUrls, "dark");

        expect(icon.getAttribute("part")).toBe("source-icon");
    });

    it("renders a Font Awesome icon for an fa:// URL", () => {
        const icon = renderIcon("Key", "fa://fa-key", null, "dark");

        expect(icon.tagName).toBe("I");
        expect(icon.classList.contains("fa-key")).toBe(true);
    });

    it("renders a placeholder icon when the source has no icon", () => {
        const icon = renderIcon("Source", null, null, "light");

        expect(icon.classList.contains("fa-share-square")).toBe(true);
    });
});
