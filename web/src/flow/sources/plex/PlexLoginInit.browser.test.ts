import { CapturedMessages, captureMessages } from "../../../../test/lit/messages.js";

import { PlexAPIClient } from "#common/helpers/plex";

import { PlexLoginInit } from "#flow/sources/plex/PlexLoginInit";
import { readPendingSignIn, writePendingSignIn } from "#flow/sources/plex/storage";
import { StageHost } from "#flow/types";

import {
    JSONApiResponse,
    PlexAuthenticationChallenge,
    RedirectChallengeFromJSON,
    SourcesApi,
} from "@goauthentik/api";

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

/**
 * The redeem endpoint's response, answering with `challenge` in the server's
 * snake_case wire format, shaped as the generated client returns it.
 */
function redeemAnswer(challenge: object) {
    return new JSONApiResponse(Response.json(challenge), RedirectChallengeFromJSON);
}

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
        .spyOn(SourcesApi.prototype, "sourcesPlexRedeemTokenCreateRaw")
        .mockImplementation(async () =>
            redeemAnswer({ component: "xak-flow-redirect", to: "/if/user/" }),
        );
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
 * Mount the stage as the browser sees it coming back from app.plex.tv: the page
 * was loaded through the forwardUrl, so it carries the return marker, and the
 * pin this session left with is waiting in storage.
 */
function createReturningStage(pin = 42): PlexLoginInit {
    writePendingSignIn({ slug: "plex", pin });
    history.replaceState(null, "", "?plex_return=1");

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
                `${window.location.origin}/if/flow/login/?next=%2Fapplication%2Fo%2Fauthorize%2F&plex_return=1`,
            );
        });

        it("adds the return marker without re-encoding the rest of the query string", async () => {
            // URLSearchParams would turn `+` into `%2B` and `%7E` into `~`, which
            // changes what `next` decodes to on the way back.
            history.replaceState(
                null,
                "",
                "/if/flow/login/?next=%2Fapplication%2Fo%2Fauthorize%2F%3Fscope%3Dopenid+email%7E",
            );

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(forwardUrlOf(navigate.mock.calls[0][0])).toBe(
                `${window.location.origin}/if/flow/login/?next=%2Fapplication%2Fo%2Fauthorize%2F%3Fscope%3Dopenid+email%7E&plex_return=1`,
            );
        });

        it("does not put the pin in the forwardUrl", async () => {
            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            // Exactly the page the stage was on plus the return marker: the
            // runner's own URL can contain any digits, so a substring check
            // proves nothing.
            const { origin, pathname, search } = window.location;
            const separator = search ? "&" : "?";

            expect(forwardUrlOf(navigate.mock.calls[0][0])).toBe(
                `${origin}${pathname}${search}${separator}plex_return=1`,
            );
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
                history.replaceState(null, "", "?plex_return=1");

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
            history.replaceState(null, "", "?plex_return=1");

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(pinStatus).not.toHaveBeenCalled();
            expect(getPin).toHaveBeenCalledOnce();
        });

        it("starts a fresh round trip over a pin left by one that never came back", async () => {
            // The user reached Plex and left without being sent back (the Back
            // button, an expired Plex page, a typed URL), then started a fresh
            // sign-in in the same tab. No return marker, so the stored pin is
            // stale and must not be reported as a cancelled sign-in.
            writePendingSignIn({ slug: "plex", pin: 7 });
            sessionStorage.setItem(ATTEMPT_KEY, "1");

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(pinStatus).not.toHaveBeenCalled();
            expect(stage.shadowRoot?.textContent).not.toContain("cancelled or timed out");
            expect(navigate.mock.calls[0][1]).toBe(true);
            expect(readPendingSignIn()).toEqual({ slug: "plex", pin: 42 });
        });

        it("removes the return marker from the address bar and keeps the rest", async () => {
            writePendingSignIn({ slug: "plex", pin: 42 });

            history.replaceState(
                null,
                "",
                "/if/flow/login/?next=%2Fapplication%2Fo%2Fauthorize%2F%3Fscope%3Dopenid+email%7E&plex_return=1",
            );

            const stage = createStage();

            await settled(stage, () => expect(navigate).toHaveBeenCalledOnce());

            expect(pinStatus).toHaveBeenCalledWith("client-id", 42);

            expect(window.location.search).toBe(
                "?next=%2Fapplication%2Fo%2Fauthorize%2F%3Fscope%3Dopenid+email%7E",
            );
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

        it("hands a denied sign-in to the flow executor instead of navigating", async () => {
            // Access denied answers 200 with a challenge that has no `to`.
            // Following it would send the browser to /if/flow/<slug>/undefined.
            redeem.mockImplementation(async () =>
                redeemAnswer({ component: "ak-stage-access-denied", error_message: "Not allowed" }),
            );

            const stage = createReturningStage();

            await settled(stage, () => expect(stage.host.challenge).toBeDefined());

            expect(stage.host.challenge).toMatchObject({
                component: "ak-stage-access-denied",
                errorMessage: "Not allowed",
            });

            expect(navigate).not.toHaveBeenCalled();
            expect(stage.errorMessage).toBeUndefined();
        });

        it("keeps the body of a page answer the typed client would drop", async () => {
            // A source without an enrollment flow answers with a rendered page.
            redeem.mockImplementation(async () =>
                redeemAnswer({ component: "xak-flow-shell", body: "<p>No enrollment flow</p>" }),
            );

            const stage = createReturningStage();

            await settled(stage, () => expect(stage.host.challenge).toBeDefined());

            expect(stage.host.challenge).toMatchObject({
                component: "xak-flow-shell",
                body: "<p>No enrollment flow</p>",
            });

            expect(navigate).not.toHaveBeenCalled();
        });

        it("offers a retry for a non-redirect answer when there is no flow executor", async () => {
            redeem.mockImplementation(async () =>
                redeemAnswer({ component: "ak-stage-access-denied", error_message: "Not allowed" }),
            );

            writePendingSignIn({ slug: "plex", pin: 42 });
            history.replaceState(null, "", "?plex_return=1");

            const stage = document.createElement("ak-flow-source-plex");

            stage.challenge = challenge;
            document.body.append(stage);
            mounted.push(stage);

            await settled(stage, () => expect(continueButton(stage)).toBeDefined());

            expect(stage.shadowRoot?.textContent).toContain("completing the login failed");
            expect(navigate).not.toHaveBeenCalled();
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
