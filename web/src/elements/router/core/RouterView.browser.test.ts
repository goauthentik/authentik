import { formatSpanName, RouterView } from "./RouterView.js";

import { getRouterConfig, initRouter, resetRouterConfig } from "#elements/router/core/config";
import { Route } from "#elements/router/core/Route";

import { page } from "@vitest/browser/context";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { html } from "lit";

const PREFIX = "/if/user/";

function makeRoutes(): Route[] {
    return [
        new Route("/", () => html`<h1>User Home</h1>`, "home"),
        new Route("/settings", () => html`<h1>Settings Page</h1>`, "settings"),
        new Route("/x", () => html`<h1>X Page</h1>`, "x"),
        new Route("/link", () => html`<a href="/if/user/settings">Go to settings</a>`, "link"),
        new Route("/boom", () => Promise.reject(new Error("kaboom")), "boom"),
    ];
}

interface MountInit {
    url: string;
    routes?: Route[];
    prefix?: string;
    defaultPath?: string;
}

const mountedContainers: HTMLElement[] = [];

function mountView(init: MountInit): RouterView {
    history.replaceState(null, "", init.url);

    const container = document.createElement("div");
    mountedContainers.push(container);
    document.body.append(container);

    // @ts-expect-error `renderLit` is added to `page` by test/lit/setup.js.
    page.renderLit(
        html`<ak-router-view
            .routes=${init.routes ?? makeRoutes()}
            .prefix=${init.prefix ?? PREFIX}
            .defaultPath=${init.defaultPath ?? "/"}
        ></ak-router-view>`,
        container,
    );

    return container.querySelector<RouterView>("ak-router-view")!;
}

describe("ak-router-view", () => {
    beforeEach(() => {
        initRouter({ base: "/", interfaceName: "user" });
    });

    afterEach(() => {
        // The shared `renderLit` helper does not track containers for cleanup, so
        // remove them here. Detaching each container fires the outlet's
        // `disconnectedCallback`, tearing down its global click/popstate/navigate
        // listeners so a prior test's outlet cannot re-render into the next test.
        while (mountedContainers.length) mountedContainers.pop()!.remove();

        resetRouterConfig();
        history.replaceState(null, "", "/");
    });

    test("registers the custom element", () => {
        expect(customElements.get("ak-router-view")).toBe(RouterView);
    });

    test("renders the route matched from the pathname", async () => {
        mountView({ url: "/if/user/settings" });

        await expect.element(page.getByText("Settings Page")).toBeInTheDocument();
    });

    test("strips the prefix down to the interface root", async () => {
        mountView({ url: "/if/user/" });

        await expect.element(page.getByText("User Home")).toBeInTheDocument();
    });

    test("replace-redirects the interface root to a non-root defaultPath", async () => {
        mountView({ url: "/if/user/", defaultPath: "/settings" });

        await expect.element(page.getByText("Settings Page")).toBeInTheDocument();
        expect(window.location.pathname).toBe("/if/user/settings");
    });

    test("falls back to the 404 element while preserving the URL", async () => {
        mountView({ url: "/if/user/does-not-exist" });

        await expect.element(page.getByText(/was not found/i)).toBeInTheDocument();
        expect(window.location.pathname).toBe("/if/user/does-not-exist");
    });

    test("intercepts an in-prefix anchor click and re-renders via pushState", async () => {
        mountView({ url: "/if/user/link" });

        await expect.element(page.getByText("Go to settings")).toBeInTheDocument();
        await page.getByText("Go to settings").click();

        await expect.element(page.getByText("Settings Page")).toBeInTheDocument();
        expect(window.location.pathname).toBe("/if/user/settings");
    });

    test("re-renders on popstate", async () => {
        mountView({ url: "/if/user/settings" });
        await expect.element(page.getByText("Settings Page")).toBeInTheDocument();

        history.replaceState(null, "", "/if/user/");
        window.dispatchEvent(new PopStateEvent("popstate"));

        await expect.element(page.getByText("User Home")).toBeInTheDocument();
    });

    test("translates a legacy hash route at boot and renders the path", async () => {
        mountView({ url: "/if/user/#/x;a=1" });

        await expect.element(page.getByText("X Page")).toBeInTheDocument();
        expect(window.location.pathname).toBe("/if/user/x");
        expect(window.location.search).toBe("?a=1");
    });

    test("renders the error state when a route rejects, without an unhandled rejection", async () => {
        const rejections: PromiseRejectionEvent[] = [];
        const onRejection = (event: PromiseRejectionEvent) => rejections.push(event);
        window.addEventListener("unhandledrejection", onRejection);

        try {
            mountView({ url: "/if/user/boom" });

            await expect.element(page.getByText("kaboom")).toBeInTheDocument();
            expect(rejections, "no unhandled rejection escaped the outlet").toHaveLength(0);
        } finally {
            window.removeEventListener("unhandledrejection", onRejection);
        }
    });

    test("reads live config through the click-interceptor scope", () => {
        // Guards the scope getter contract Plan 3b relies on.
        expect(getRouterConfig()).toEqual({ base: "/", interfaceName: "user" });
    });
});

describe("formatSpanName", () => {
    test("joins a bare route name onto the prefix with a single slash", () => {
        expect(formatSpanName("/if/user/", "library", "/ignored")).toBe("/if/user/library");
    });

    test("collapses a slash-carrying default route name", () => {
        expect(formatSpanName("/if/user/", "/x", "/ignored")).toBe("/if/user/x");
    });

    test("passes the pathname through for the null (404) branch", () => {
        expect(formatSpanName("/if/user/", null, "/if/user/does-not-exist")).toBe(
            "/if/user/does-not-exist",
        );
    });

    test("handles a non-root base prefix", () => {
        expect(formatSpanName("/auth/if/user/", "settings", "/ignored")).toBe(
            "/auth/if/user/settings",
        );
    });
});
