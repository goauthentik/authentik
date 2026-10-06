import "#admin/sources/plex/PlexSourceForm";
import { CapturedMessages, captureMessages } from "../../../../test/lit/messages.js";

import { PlexAPIClient, PlexResource } from "#common/helpers/plex";

import type { PlexSourceForm } from "#admin/sources/plex/PlexSourceForm";

import { PlexSource } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const AUTH_URL = "https://app.plex.tv/auth#?clientID=client-id&code=pin-code";

const server: PlexResource = {
    name: "Media",
    provides: "server",
    clientIdentifier: "server-id",
    owned: true,
};

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

let popup: FakePopup;
let open: ReturnType<typeof vi.spyOn>;
let getPin: ReturnType<typeof vi.spyOn>;
let pinPoll: ReturnType<typeof vi.spyOn>;
let getServers: ReturnType<typeof vi.spyOn>;
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
    getServers = vi.spyOn(PlexAPIClient.prototype, "getServers").mockResolvedValue([server]);
});

afterEach(() => {
    toasts.cleanup();
    vi.restoreAllMocks();
});

/**
 * The form is left unmounted: its other fields fetch flows, mappings and files
 * from the API on connect, none of which the Plex sign-in touches.
 */
function createForm(): PlexSourceForm {
    const form = document.createElement("ak-source-plex-form");

    form.instance = { clientId: "client-id" } as PlexSource;

    return form;
}

describe("PlexSourceForm.doAuth", () => {
    describe("popup", () => {
        it("opens the popup before the pin request resolves", () => {
            getPin.mockReturnValue(new Promise(() => {}));

            const form = createForm();

            // Not awaited: window.open must already have run by the time
            // doAuth first yields, or the click's user activation is gone.
            void form.doAuth();

            expect(open).toHaveBeenCalledOnce();
            expect(open.mock.calls[0][0]).toBe("about:blank");
        });

        it("points the popup at Plex once the pin arrives", async () => {
            await createForm().doAuth();

            expect(getPin).toHaveBeenCalledWith("client-id");
            expect(popup.location.replace).toHaveBeenCalledWith(AUTH_URL);
        });

        it("leaves a popup the user already closed alone", async () => {
            const form = createForm();

            getPin.mockImplementation(async () => {
                popup.closed = true;

                return { authUrl: AUTH_URL, pin: { id: 42, code: "pin-code" } };
            });

            await form.doAuth();

            expect(popup.location.replace).not.toHaveBeenCalled();
        });
    });

    describe("authorizing", () => {
        it("keeps the token and closes the popup", async () => {
            const form = createForm();

            await form.doAuth();

            expect(pinPoll).toHaveBeenCalledWith("client-id", 42);
            expect(form.plexToken).toBe("plex-token");
            expect(popup.close).toHaveBeenCalled();
        });

        it("loads the servers the token can see", async () => {
            const form = createForm();

            await form.doAuth();

            expect(getServers).toHaveBeenCalledOnce();
            expect(form.plexResources).toEqual([server]);
            expect(toasts.messages).toEqual([]);
        });
    });

    describe("failures", () => {
        it("closes the popup and reports the error when the pin request fails", async () => {
            getPin.mockRejectedValue(new Error("plex.tv unreachable"));

            await createForm().doAuth();

            expect(popup.close).toHaveBeenCalled();
            expect(toasts.messages).toHaveLength(1);
            expect(toasts.messages[0].message).toContain("plex.tv unreachable");
            expect(pinPoll).not.toHaveBeenCalled();
        });

        it("closes the popup and keeps the old token when the pin expires", async () => {
            pinPoll.mockRejectedValue(new Error("Invalid response code"));

            const form = createForm();

            form.plexToken = "previous-token";

            await form.doAuth();

            expect(popup.close).toHaveBeenCalled();
            expect(toasts.messages[0].message).toContain("Invalid response code");
            expect(form.plexToken).toBe("previous-token");
            expect(getServers).not.toHaveBeenCalled();
        });

        it("reports the error when loading servers fails", async () => {
            getServers.mockRejectedValue(new Error("resources unavailable"));

            await createForm().doAuth();

            expect(toasts.messages).toHaveLength(1);
            expect(toasts.messages[0].message).toContain("resources unavailable");
        });

        it("reports the expired pin when the browser blocked the popup", async () => {
            open.mockReturnValue(null);
            pinPoll.mockRejectedValue(new Error("Invalid response code"));

            await createForm().doAuth();

            expect(toasts.messages).toHaveLength(1);
            expect(toasts.messages[0].message).toContain("Invalid response code");
        });
    });
});
