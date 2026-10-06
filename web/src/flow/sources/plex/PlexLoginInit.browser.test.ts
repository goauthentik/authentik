import { CapturedMessages, captureMessages } from "../../../../test/lit/messages.js";

import { PlexAPIClient } from "#common/helpers/plex";

import { PlexLoginInit } from "#flow/sources/plex/PlexLoginInit";
import { readPendingSignIn, writePendingSignIn } from "#flow/sources/plex/storage";
import { StageHost } from "#flow/types";

import { PlexAuthenticationChallenge, SourcesApi } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const ATTEMPT_KEY = "authentik-plex-attempt";

const challenge: PlexAuthenticationChallenge = {
    clientId: "client-id",
    slug: "plex",
};

const mounted: HTMLElement[] = [];
const originalURL = window.location.href;

let navigate: ReturnType<typeof vi.spyOn>;
let getPin: ReturnType<typeof vi.spyOn>;
let pinStatus: ReturnType<typeof vi.spyOn>;
let redeem: ReturnType<typeof vi.spyOn>;
let toasts: CapturedMessages;

beforeEach(() => {
    sessionStorage.clear();

    toasts = captureMessages();

    // The stage's only way off the page. Stubbed so a redirect is something to
    // assert on rather than the test runner navigating away.
    navigate = vi
        .spyOn(PlexLoginInit.prototype as unknown as { navigate: () => void }, "navigate")
        .mockImplementation(() => {});

    getPin = vi.spyOn(PlexAPIClient, "getPin").mockResolvedValue({
        authUrl: "https://app.plex.tv/auth#?unused",
        pin: { id: 42, code: "pin-code" },
    });

    pinStatus = vi.spyOn(PlexAPIClient, "pinStatus").mockResolvedValue("plex-token");

    redeem = vi
        .spyOn(SourcesApi.prototype, "sourcesPlexRedeemTokenCreate")
        .mockResolvedValue({ to: "/if/user/" });
});

afterEach(() => {
    toasts.cleanup();
    vi.restoreAllMocks();
    sessionStorage.clear();
    history.replaceState(null, "", originalURL);

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

function createStage(): PlexLoginInit {
    const stage = document.createElement("ak-flow-source-plex");

    stage.host = { submit: vi.fn() } as unknown as StageHost;
    stage.challenge = challenge;

    document.body.append(stage);
    mounted.push(stage);

    return stage;
}

/**
 * Mount the stage as the browser sees it coming back from app.plex.tv: the pin
 * this session left with is waiting in storage.
 */
function createReturningStage(pin = 42): PlexLoginInit {
    writePendingSignIn({ slug: "plex", pin });

    return createStage();
}

const continueButton = (stage: HTMLElement) =>
    Array.from(stage.shadowRoot?.querySelectorAll("button") ?? []).find((button) =>
        button.textContent?.includes("Continue to Plex"),
    );

const spinning = (stage: HTMLElement) =>
    stage.shadowRoot?.querySelector("ak-empty-state")?.hasAttribute("loading") ?? false;

/** The forwardUrl Plex was told to send the browser back to. */
function forwardUrlOf(url: string): string | null {
    return new URLSearchParams(new URL(url).hash.slice(2)).get("forwardUrl");
}

async function settled(stage: PlexLoginInit, assertion: () => void): Promise<void> {
    await vi.waitFor(assertion);
    await stage.updateComplete;
}

describe("PlexLoginInit", () => {
    describe("outbound leg", () => {
        it("replaces the page with app.plex.tv on first visit", async () => {
            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            const [url, replace] = navigate.mock.calls[0];

            expect(url.startsWith("https://app.plex.tv/auth#?")).toBe(true);
            expect(replace).toBe(true);
            expect(getPin).toHaveBeenCalledWith("client-id");
        });

        it("stores the minted pin and counts the attempt before leaving", async () => {
            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(readPendingSignIn()).toEqual({ slug: "plex", pin: 42 });
            expect(sessionStorage.getItem(ATTEMPT_KEY)).toBe("1");
        });

        it("keeps the flow's query string in the forwardUrl", async () => {
            history.replaceState(
                null,
                "",
                "/if/flow/login/?next=%2Fapplication%2Fo%2Fauthorize%2F",
            );

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(forwardUrlOf(navigate.mock.calls[0][0])).toBe(
                `${window.location.origin}/if/flow/login/?next=%2Fapplication%2Fo%2Fauthorize%2F`,
            );
        });

        it("does not put the pin in the forwardUrl", async () => {
            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            // Exactly the page the stage was on, with nothing added: the runner's
            // own URL can contain any digits, so a substring check proves nothing.
            const { origin, pathname, search } = window.location;

            expect(forwardUrlOf(navigate.mock.calls[0][0])).toBe(`${origin}${pathname}${search}`);
        });

        it("ignores a pin carried in the URL and starts a fresh round trip", async () => {
            // A crafted link handing over an attacker-authorized pin must not be
            // redeemed: only storage written by this session counts.
            history.replaceState(null, "", "?pin=1337&plex-pin=1337");

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(pinStatus).not.toHaveBeenCalled();
            expect(redeem).not.toHaveBeenCalled();
            expect(getPin).toHaveBeenCalledOnce();
        });

        it("offers a retry when minting a pin fails", async () => {
            getPin.mockRejectedValue(new Error("plex.tv unreachable"));

            const stage = createStage();

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(stage.shadowRoot?.textContent).toContain("Could not start sign-in with Plex.");
            expect(toasts.messages[0]?.message).toContain("plex.tv unreachable");
            expect(spinning(stage)).toBe(false);
            expect(navigate).not.toHaveBeenCalled();
        });

        it("stays put and says so when session storage is blocked", async () => {
            vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
                throw new DOMException("blocked", "SecurityError");
            });

            const stage = createStage();

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(stage.shadowRoot?.textContent).toContain("needs session storage");
            expect(navigate).not.toHaveBeenCalled();
        });
    });

    describe("redirect cap", () => {
        it("does not redirect automatically once the attempt cap is reached", async () => {
            sessionStorage.setItem(ATTEMPT_KEY, "2");

            const stage = createStage();

            await settled(stage, () =>
                expect(stage.shadowRoot?.textContent).toContain(
                    "Not redirecting to Plex automatically.",
                ),
            );

            expect(spinning(stage)).toBe(false);
            expect(getPin).not.toHaveBeenCalled();
            expect(navigate).not.toHaveBeenCalled();
        });

        it("assigns rather than replaces when the button is clicked past the cap", async () => {
            sessionStorage.setItem(ATTEMPT_KEY, "2");

            const stage = createStage();

            await stage.updateComplete;
            continueButton(stage)!.click();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(navigate.mock.calls[0][1]).toBe(false);
            expect(readPendingSignIn()).toEqual({ slug: "plex", pin: 42 });
        });

        it("does not leave for Plex from the button when session storage is blocked", async () => {
            sessionStorage.setItem(ATTEMPT_KEY, "2");

            const stage = createStage();

            await stage.updateComplete;

            vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
                throw new DOMException("blocked", "SecurityError");
            });

            continueButton(stage)!.click();

            await settled(stage, () =>
                expect(stage.shadowRoot?.textContent).toContain("needs session storage"),
            );

            expect(navigate).not.toHaveBeenCalled();
        });

        it("still redirects automatically after backing out at Plex twice", async () => {
            // Two round trips that each came back cancelled.
            for (let i = 0; i < 2; i++) {
                const outbound = createStage();

                await settled(outbound, () => expect(navigate).toHaveBeenCalledTimes(i + 1));
                outbound.remove();

                pinStatus.mockResolvedValueOnce(undefined);

                const returning = createStage();

                await settled(returning, () => expect(continueButton(returning)).toBeDefined());
                returning.remove();
            }

            // A fresh sign-in in the same tab.
            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledTimes(3));

            expect(navigate.mock.calls[2][1]).toBe(true);
            expect(stage.shadowRoot?.textContent).not.toContain("Not redirecting");
        });
    });

    describe("return leg", () => {
        it("leaves another source's pending sign-in alone", async () => {
            writePendingSignIn({ slug: "other-plex", pin: 7 });

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(pinStatus).not.toHaveBeenCalled();
            expect(getPin).toHaveBeenCalledOnce();
        });

        it("redeems the token and continues the flow", async () => {
            const stage = createReturningStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(pinStatus).toHaveBeenCalledWith("client-id", 42);

            expect(redeem).toHaveBeenCalledWith({
                plexTokenRedeemRequest: { plexToken: "plex-token" },
                slug: "plex",
            });

            expect(navigate).toHaveBeenCalledWith("/if/user/");
            expect(getPin).not.toHaveBeenCalled();
        });

        it("consumes the stored pin and the attempt count", async () => {
            sessionStorage.setItem(ATTEMPT_KEY, "1");

            const stage = createReturningStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(readPendingSignIn()).toBeNull();
            expect(sessionStorage.getItem(ATTEMPT_KEY)).toBeNull();
        });

        it("checks the pin once instead of polling", async () => {
            pinStatus.mockResolvedValue(undefined);

            const stage = createReturningStage();

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(pinStatus).toHaveBeenCalledOnce();
        });

        it("offers a retry when the user backed out at Plex", async () => {
            pinStatus.mockResolvedValue(undefined);

            const stage = createReturningStage();

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(stage.shadowRoot?.textContent).toContain("cancelled or timed out");
            expect(spinning(stage)).toBe(false);
            expect(redeem).not.toHaveBeenCalled();
            expect(navigate).not.toHaveBeenCalled();
        });

        it("offers a retry when the pin has expired", async () => {
            pinStatus.mockRejectedValue(new Error("Invalid response code"));

            const stage = createReturningStage();

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(stage.shadowRoot?.textContent).toContain("cancelled or timed out");
            expect(redeem).not.toHaveBeenCalled();
        });

        it("offers a retry when redeeming the token fails", async () => {
            redeem.mockRejectedValue(new Error("redeem failed"));

            const stage = createReturningStage();

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(stage.shadowRoot?.textContent).toContain("completing the login failed");
            expect(toasts.messages[0]?.message).toContain("redeem failed");
            expect(navigate).not.toHaveBeenCalled();
        });

        it("starts a new round trip with a fresh pin from the retry button", async () => {
            pinStatus.mockResolvedValue(undefined);

            const stage = createReturningStage(7);

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            continueButton(stage)!.click();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(getPin).toHaveBeenCalledOnce();
            expect(readPendingSignIn()).toEqual({ slug: "plex", pin: 42 });
            expect(spinning(stage)).toBe(true);
        });
    });
});
