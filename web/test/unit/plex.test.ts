import { PlexAPIClient, popupCenterScreen } from "#common/helpers/plex";

import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
    vi.unstubAllGlobals();
});

/**
 * Split an app.plex.tv auth URL into its fragment parameters.
 *
 * The parameters live after `#?`, so `URL.searchParams` never sees them.
 */
function fragmentParams(url: string): URLSearchParams {
    const { hash } = new URL(url);

    expect(hash.startsWith("#?")).toBe(true);

    return new URLSearchParams(hash.slice(2));
}

describe("PlexAPIClient.authUrl", () => {
    it("uses the #? fragment form that forwardUrl is known to work with", () => {
        const url = PlexAPIClient.authUrl("client", "code");

        expect(url.startsWith("https://app.plex.tv/auth#?")).toBe(true);
        expect(url).not.toContain("#!?");
    });

    it("identifies authentik as the product on plex.tv", () => {
        const params = fragmentParams(PlexAPIClient.authUrl("client", "code"));

        expect(params.get("context[device][product]")).toBe("authentik");
    });

    it("omits forwardUrl when no return URL is given", () => {
        const params = fragmentParams(PlexAPIClient.authUrl("client", "code"));

        expect(params.has("forwardUrl")).toBe(false);
    });

    it("round-trips a forwardUrl carrying its own query string", () => {
        const returnUrl =
            "https://authentik.example/if/flow/default-authentication-flow/?next=%2Fapplication%2Fo%2Fauthorize%2F%3Fclient_id%3Dx%26state%3Dy";

        const params = fragmentParams(PlexAPIClient.authUrl("client", "code", returnUrl));

        expect(params.get("forwardUrl")).toBe(returnUrl);
    });

    it("encodes a client ID and code that would otherwise break out of their parameter", () => {
        const params = fragmentParams(PlexAPIClient.authUrl("a&forwardUrl=evil", "c#d"));

        expect(params.get("clientID")).toBe("a&forwardUrl=evil");
        expect(params.get("code")).toBe("c#d");
        expect(params.has("forwardUrl")).toBe(false);
    });
});

describe("PlexAPIClient.getPin", () => {
    it("returns the minted pin with a popup auth URL that has no forwardUrl", async () => {
        const fetchMock = vi
            .fn()
            .mockResolvedValue(new Response(JSON.stringify({ id: 42, code: "pin-code" })));

        vi.stubGlobal("fetch", fetchMock);

        const { authUrl, pin } = await PlexAPIClient.getPin("client");

        expect(pin).toEqual({ id: 42, code: "pin-code" });
        expect(fetchMock.mock.calls[0][1].headers["X-Plex-Client-Identifier"]).toBe("client");

        const params = fragmentParams(authUrl);

        expect(params.get("code")).toBe("pin-code");
        expect(params.has("forwardUrl")).toBe(false);
    });
});

describe("PlexAPIClient.pinStatus", () => {
    it("returns the token of an authorized pin", async () => {
        vi.stubGlobal(
            "fetch",
            vi
                .fn()
                .mockResolvedValue(
                    new Response(JSON.stringify({ id: 42, code: "c", authToken: "token" })),
                ),
        );

        await expect(PlexAPIClient.pinStatus("client", 42)).resolves.toBe("token");
    });

    it("returns undefined for a pin that has not been authorized", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 42, code: "c" }))),
        );

        await expect(PlexAPIClient.pinStatus("client", 42)).resolves.toBeUndefined();
    });

    it("throws for an expired pin", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 404 })));

        await expect(PlexAPIClient.pinStatus("client", 42)).rejects.toThrow();
    });
});

describe("popupCenterScreen", () => {
    it("opens the window synchronously, inside the caller's task", () => {
        const popup = {} as Window;
        const open = vi.fn().mockReturnValue(popup);

        vi.stubGlobal("screen", { width: 1000, height: 800 });
        vi.stubGlobal("window", { open });

        const result = popupCenterScreen("about:blank", "plex auth", 550, 700);

        // A Promise here would mean window.open ran after the click's user
        // activation had already lapsed.
        expect(result).toBe(popup);
        expect(open).toHaveBeenCalledOnce();
        expect(open.mock.calls[0][0]).toBe("about:blank");
        expect(open.mock.calls[0][2]).toContain("width=550,height=700");
    });
});
