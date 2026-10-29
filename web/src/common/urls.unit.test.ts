import { staticURL, websocketURL } from "#common/urls";

import { afterEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ base: "", relBase: "" }));

vi.mock("#common/global", () => ({
    globalAK: () => ({ api }),
}));

function serveFrom(webPath: string) {
    api.base = `http://authentik.company${webPath}`;
    api.relBase = webPath;
}

describe("websocketURL", () => {
    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("resolves the path at the root", () => {
        serveFrom("/");
        vi.stubGlobal("window", { location: { protocol: "http:" } });

        expect(websocketURL("ws/rac/a-token/")).toBe("ws://authentik.company/ws/rac/a-token/");
    });

    it("resolves the path below the web base path", () => {
        serveFrom("/authentik/");
        vi.stubGlobal("window", { location: { protocol: "https:" } });

        expect(websocketURL("ws/rac/a-token/")).toBe(
            "wss://authentik.company/authentik/ws/rac/a-token/",
        );
    });
});

describe("staticURL", () => {
    it("resolves the file at the root", () => {
        serveFrom("/");

        expect(staticURL("/static/dist/assets/icons/icon.png")).toBe(
            "/static/dist/assets/icons/icon.png",
        );
    });

    it("resolves the file below the web base path", () => {
        serveFrom("/authentik/");

        expect(staticURL("/static/dist/assets/icons/icon.png")).toBe(
            "/authentik/static/dist/assets/icons/icon.png",
        );
    });
});
