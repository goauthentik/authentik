import "#elements/user/sources/SourceSettingsPlex";
import { CapturedMessages, captureMessages } from "../../../../test/lit/messages.js";

import { EVENT_REFRESH } from "#common/constants";
import { PlexAPIClient } from "#common/helpers/plex";

import type { SourceSettingsPlex } from "#elements/user/sources/SourceSettingsPlex";

import { SourcesApi } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const AUTH_URL = "https://app.plex.tv/auth#?clientID=client-id&code=pin-code";

interface FakePopup {
    closed: boolean;
    close: ReturnType<typeof vi.fn>;
    location: { replace: ReturnType<typeof vi.fn> };
}

function popupOf(): FakePopup {
    const popup: FakePopup = {
        closed: false,
        close: vi.fn(() => {
            popup.closed = true;
        }),
        location: { replace: vi.fn() },
    };

    return popup;
}

/** A promise along with the means to settle it from the test. */
function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason: unknown) => void;

    const promise = new Promise<T>((res, rej) => {
        resolve = res;
        reject = rej;
    });

    return { promise, resolve, reject };
}

const mounted: HTMLElement[] = [];

let popup: FakePopup;
let open: ReturnType<typeof vi.spyOn>;
let getPin: ReturnType<typeof vi.spyOn>;
let pinPoll: ReturnType<typeof vi.spyOn>;
let redeem: ReturnType<typeof vi.spyOn>;
let refreshes: ReturnType<typeof vi.fn<(event: Event) => void>>;
let toasts: CapturedMessages;

beforeEach(() => {
    toasts = captureMessages();
    popup = popupOf();

    open = vi.spyOn(window, "open").mockReturnValue(popup as unknown as Window);

    getPin = vi.spyOn(PlexAPIClient, "getPin").mockResolvedValue({
        authUrl: AUTH_URL,
        pin: { id: 42, code: "pin-code" },
    });

    pinPoll = vi.spyOn(PlexAPIClient, "pinPoll").mockResolvedValue("plex-token");

    redeem = vi
        .spyOn(SourcesApi.prototype, "sourcesPlexRedeemTokenAuthenticatedCreate")
        .mockResolvedValue(undefined);

    refreshes = vi.fn<(event: Event) => void>();
    document.body.addEventListener(EVENT_REFRESH, refreshes);
});

afterEach(() => {
    document.body.removeEventListener(EVENT_REFRESH, refreshes);
    toasts.cleanup();
    vi.restoreAllMocks();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

async function createSettings(): Promise<SourceSettingsPlex> {
    const settings = document.createElement("ak-user-settings-source-plex");

    settings.allowConfiguration = true;

    settings.source = {
        objectUid: "plex-source",
        component: "ak-user-settings-source-plex",
        title: "Plex",
        configureUrl: "client-id",
    };

    document.body.append(settings);
    mounted.push(settings);

    await settings.updateComplete;

    return settings;
}

function connect(settings: SourceSettingsPlex): void {
    const button = Array.from(settings.shadowRoot?.querySelectorAll("button") ?? []).find(
        (candidate) => candidate.textContent?.includes("Connect"),
    );

    expect(button).toBeDefined();

    button!.click();
}

describe("SourceSettingsPlex", () => {
    describe("popup", () => {
        it("opens the popup inside the click, before the pin request resolves", async () => {
            getPin.mockReturnValue(new Promise(() => {}));

            const settings = await createSettings();

            connect(settings);

            // Checked synchronously after the click: any await before
            // window.open would leave it uncalled here, and the browser would
            // have blocked the popup for lack of user activation.
            expect(open).toHaveBeenCalledOnce();
            expect(open.mock.calls[0][0]).toBe("about:blank");
        });

        it("points the popup at Plex once the pin arrives", async () => {
            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(popup.location.replace).toHaveBeenCalledWith(AUTH_URL));

            expect(getPin).toHaveBeenCalledWith("client-id");
        });

        it("leaves a popup the user already closed alone", async () => {
            const pin = deferred<Awaited<ReturnType<typeof PlexAPIClient.getPin>>>();

            getPin.mockReturnValue(pin.promise);

            const settings = await createSettings();

            connect(settings);
            popup.closed = true;
            pin.resolve({ authUrl: AUTH_URL, pin: { id: 42, code: "pin-code" } });

            await vi.waitFor(() => expect(pinPoll).toHaveBeenCalled());

            expect(popup.location.replace).not.toHaveBeenCalled();
        });

        it("closes the popup once the pin is authorized", async () => {
            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(popup.close).toHaveBeenCalled());

            expect(pinPoll).toHaveBeenCalledWith("client-id", 42);
        });
    });

    describe("connecting", () => {
        it("redeems the token against this source", async () => {
            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(redeem).toHaveBeenCalledOnce());

            expect(redeem).toHaveBeenCalledWith({
                plexTokenRedeemRequest: { plexToken: "plex-token" },
                slug: "plex-source",
            });
        });

        it("refreshes the source list only after the connection is saved", async () => {
            const saved = deferred<void>();

            redeem.mockReturnValue(saved.promise);

            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(redeem).toHaveBeenCalledOnce());

            expect(refreshes).not.toHaveBeenCalled();

            saved.resolve();

            await vi.waitFor(() => expect(refreshes).toHaveBeenCalledOnce());

            expect(toasts.messages).toEqual([]);
        });
    });

    describe("failures", () => {
        it("closes the popup and reports the error when the pin request fails", async () => {
            getPin.mockRejectedValue(new Error("plex.tv unreachable"));

            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(toasts.messages).toHaveLength(1));

            expect(popup.close).toHaveBeenCalled();
            expect(toasts.messages[0].message).toContain("plex.tv unreachable");
            expect(pinPoll).not.toHaveBeenCalled();
            expect(refreshes).not.toHaveBeenCalled();
        });

        it("closes the popup and reports the error when the pin expires", async () => {
            pinPoll.mockRejectedValue(new Error("Invalid response code"));

            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(toasts.messages).toHaveLength(1));

            expect(popup.close).toHaveBeenCalled();
            expect(toasts.messages[0].message).toContain("Failed to connect source");
            expect(redeem).not.toHaveBeenCalled();
            expect(refreshes).not.toHaveBeenCalled();
        });

        it("reports the error and does not refresh when saving the connection fails", async () => {
            redeem.mockRejectedValue(new Error("redeem failed"));

            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(toasts.messages).toHaveLength(1));

            expect(toasts.messages[0].message).toContain("redeem failed");
            expect(refreshes).not.toHaveBeenCalled();
        });

        it("reports the expired pin when the browser blocked the popup", async () => {
            open.mockReturnValue(null);
            pinPoll.mockRejectedValue(new Error("Invalid response code"));

            const settings = await createSettings();

            connect(settings);

            await vi.waitFor(() => expect(toasts.messages).toHaveLength(1));

            expect(toasts.messages[0].message).toContain("Failed to connect source");
            expect(redeem).not.toHaveBeenCalled();
        });
    });
});
