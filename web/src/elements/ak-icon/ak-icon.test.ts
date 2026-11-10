import "./ak-icon.js";

import { type Icon } from "./ak-icon.js";

import { spread } from "@open-wc/lit-helpers";
import { describe, expect, it } from "vitest";
import { render } from "vitest-browser-lit";
import { Locator, locators, page } from "vitest/browser";

import { html } from "lit";

locators.extend({
    getElement() {
        return "ak-icon";
    },
    getContent() {
        return 'ak-icon >> [part="content"]';
    },
    getIcon() {
        return 'ak-icon >> [part="icon"]';
    },
});

declare module "vitest/browser" {
    interface LocatorSelectors {
        getElement(): Locator;
        getContent(): Locator;
        getIcon(): Locator;
    }
}

describe("ak-icon component", () => {
    const renderComponent = async (properties = {}) => {
        return render(html`<ak-icon ${spread(properties)}></ak-icon>`);
    };

    it("should render a basic icon", async () => {
        renderComponent({ icon: "fas fa-user" });
        const element = await page.getElement();
        const icon = await page.getIcon();
        await expect.element(element).toBeVisible();
        await expect.element(icon).toHaveClass("fas");
        await expect.element(icon).toHaveClass("fa-user");
    });

    it("should render with fallback icon when no icon is provided", async () => {
        render(html`<ak-icon></ak-icon>`);
        const icon = await page.getIcon();
        await expect.element(icon).toBeVisible();
        await expect.element(icon).toHaveAttribute("class", "fa fa-bug");
    });

    it("should render with a custom fallback icon when no icon is provided", async () => {
        render(html`<ak-icon fallback="fa fa-question"></ak-icon>`);
        const icon = await page.getIcon();
        await expect.element(icon).toBeVisible();
        await expect.element(icon).toHaveAttribute("class", "fa fa-question");
    });

    it("should resolve alias correctly", async () => {
        renderComponent({ icon: "user" });
        const icon = await page.getIcon();
        await expect.element(icon).toHaveAttribute("class", "fas fa-user");
    });

    it("should handle explicit family and icon", async () => {
        renderComponent({ family: "pf", icon: "pf-icon-cluster" });
        const icon = await page.getIcon();
        await expect.element(icon).toHaveAttribute("class", "pf pf-icon-cluster");
    });

    it("should handle space-separated icon class", async () => {
        render(html`<ak-icon icon="fas fa-home"></ak-icon>`);
        const icon = await page.getIcon();
        await expect.element(icon).toHaveAttribute("class", "fas fa-home");
    });

    it("should fallback when alias resolution fails", async () => {
        render(html`<ak-icon icon="nonexistent-icon"></ak-icon>`);
        const icon = await page.getIcon();
        await expect.element(icon).toHaveAttribute("class", "fa fa-bug");
    });

    it("should update icon when property changes", async () => {
        render(html`<ak-icon icon="user"></ak-icon>`);
        const icon = await page.getIcon();

        await expect.element(icon).toHaveAttribute("class", "fas fa-user");
        const element = await page.getElement().element();
        element.setAttribute("icon", "home");
        const newPart = await page.getIcon();
        await expect.element(newPart).toHaveAttribute("class", "fas fa-home");
    });

    it("should handle PatternFly aliases", async () => {
        render(html`<ak-icon icon="cluster"></ak-icon>`);
        const part = await page.getIcon();
        await expect.element(part).toHaveAttribute("class", "pf pf-icon-cluster");
    });

    it("should prefer explicit family over alias resolution", async () => {
        render(html`<ak-icon family="fab" icon="user"></ak-icon>`);
        const icon = await page.getIcon();
        await expect.element(icon).toHaveAttribute("class", "fab user");
    });

    it("should re-derive icon class on property changes", async () => {
        render(html`<ak-icon icon="user"></ak-icon>`);
        let icon = await page.getIcon();
        await expect(icon).toHaveAttribute("class", "fas fa-user");

        const element = await page.getElement().element();
        (element as Icon).icon = "home";
        (element as Icon).family = "pf";

        icon = await page.getIcon();
        await expect.element(icon).toHaveAttribute("class", "pf home");
    });
});
