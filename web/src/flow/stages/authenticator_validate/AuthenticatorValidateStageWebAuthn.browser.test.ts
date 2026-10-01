import "#flow/stages/authenticator_validate/AuthenticatorValidateStageWebAuthn";
import { FlowExecutor } from "#flow/FlowExecutor";
import { StageHost } from "#flow/types";

import {
    AuthenticatorValidationChallenge,
    DeviceChallenge,
    DeviceClassesEnum,
    FlowsApi,
} from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const deviceChallenge: DeviceChallenge = {
    deviceClass: DeviceClassesEnum.Webauthn,
    deviceUid: "1",
    challenge: { challenge: "AA==" },
    lastUsed: new Date(),
};

function challengeOf(
    overrides: Partial<AuthenticatorValidationChallenge> = {},
): AuthenticatorValidationChallenge {
    return {
        component: "ak-stage-authenticator-validate",
        pendingUser: "akadmin",
        pendingUserAvatar: "",
        deviceChallenges: [deviceChallenge],
        configurationStages: [],
        ...overrides,
    };
}

/**
 * A minimal stand-in for the credential an authenticator would hand back.
 *
 * The stage narrows the result with `instanceof PublicKeyCredential`, whose constructor is
 * not callable, so the stand-in borrows the real prototype. Own properties are declared
 * first, shadowing the prototype's getter-only accessors.
 */
function assertionOf(): PublicKeyCredential {
    const bytes = () => Uint8Array.from([1, 2, 3]).buffer;

    return Object.setPrototypeOf(
        {
            id: "credential-id",
            type: "public-key",
            rawId: bytes(),
            response: {
                clientDataJSON: bytes(),
                authenticatorData: bytes(),
                signature: bytes(),
                userHandle: null,
            },
            getClientExtensionResults: () => ({}),
        },
        PublicKeyCredential.prototype,
    ) as PublicKeyCredential;
}

const mounted: HTMLElement[] = [];

let submit: ReturnType<typeof vi.fn>;
let refresh: ReturnType<typeof vi.fn>;
let credentialsGet: ReturnType<typeof vi.fn>;

beforeEach(() => {
    submit = vi.fn().mockResolvedValue(true);
    refresh = vi.fn().mockResolvedValue(true);
    credentialsGet = vi.fn().mockResolvedValue(assertionOf());

    vi.stubGlobal("navigator", {
        ...navigator,
        credentials: { get: credentialsGet },
    });
});

afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

function createStage() {
    const stage = document.createElement("ak-stage-authenticator-validate-webauthn");

    stage.host = { submit, refresh } as unknown as StageHost;
    stage.deviceChallenge = deviceChallenge;

    document.body.append(stage);
    mounted.push(stage);

    return stage;
}

const retryButton = (stage: HTMLElement) =>
    Array.from(stage.shadowRoot?.querySelectorAll("button") ?? []).find((button) =>
        button.textContent?.includes("Retry authentication"),
    );

const spinning = (stage: HTMLElement) =>
    stage.shadowRoot?.querySelector("ak-empty-state")?.hasAttribute("loading") ?? false;

describe("AuthenticatorValidateStageWebAuthn", () => {
    it("renders a spinner and no retry before the first challenge", async () => {
        const stage = createStage();

        await stage.updateComplete;

        expect(stage.shadowRoot?.textContent).toContain("Authenticating...");
        expect(spinning(stage)).toBe(true);
        expect(retryButton(stage)).toBeUndefined();
    });

    it("submits the assertion and keeps spinning while the flow advances", async () => {
        const stage = createStage();

        stage.challenge = challengeOf();

        await vi.waitFor(() => expect(submit).toHaveBeenCalledOnce());
        await stage.updateComplete;

        expect(credentialsGet).toHaveBeenCalledOnce();
        expect(submit.mock.calls[0][0]).toMatchObject({ webauthn: { id: "credential-id" } });
        expect(submit.mock.calls[0][1]).toEqual({ invisible: true });

        // The regression: no retry button, no error, no flicker out of the spinner.
        expect(retryButton(stage)).toBeUndefined();
        expect(spinning(stage)).toBe(true);
    });

    it("offers retry when the ceremony fails", async () => {
        credentialsGet.mockRejectedValue(new DOMException("denied", "NotAllowedError"));

        const stage = createStage();

        stage.challenge = challengeOf();

        await vi.waitFor(() => expect(retryButton(stage)).toBeDefined());

        expect(spinning(stage)).toBe(false);
        expect(stage.shadowRoot?.textContent).toContain("cancelled or timed out");
        expect(submit).not.toHaveBeenCalled();
    });

    it("waits for a fresh server challenge before starting a single retry ceremony", async () => {
        credentialsGet.mockRejectedValue(new DOMException("denied", "NotAllowedError"));

        const stage = createStage();

        stage.challenge = challengeOf();

        await vi.waitFor(() => expect(retryButton(stage)).toBeDefined());

        credentialsGet.mockReturnValue(new Promise(() => {}));

        const retry = retryButton(stage)!;
        retry.click();
        retry.click();
        await stage.updateComplete;

        expect(refresh).toHaveBeenCalledOnce();
        expect(credentialsGet).toHaveBeenCalledOnce();

        stage.deviceChallenge = {
            ...deviceChallenge,
            challenge: { challenge: "AQ==" },
        };

        stage.challenge = challengeOf({ deviceChallenges: [stage.deviceChallenge] });
        await stage.updateComplete;

        expect(credentialsGet).toHaveBeenCalledTimes(2);

        expect(credentialsGet.mock.calls[1][0].publicKey.challenge).toEqual(Uint8Array.from([1]));
    });

    it("renders a response error instead of re-running the ceremony", async () => {
        const stage = createStage();

        stage.challenge = challengeOf({
            responseErrors: { webauthn: [{ code: "invalid", string: "Invalid assertion" }] },
        });

        await stage.updateComplete;

        expect(stage.shadowRoot?.textContent).toContain("Invalid assertion");
        expect(retryButton(stage)).toBeDefined();
        expect(credentialsGet).not.toHaveBeenCalled();
    });

    it("allows retrying a failed challenge refresh without reusing the old challenge", async () => {
        credentialsGet.mockRejectedValue(new DOMException("denied", "NotAllowedError"));
        refresh.mockRejectedValueOnce(new Error("Network unavailable"));

        const stage = createStage();
        stage.challenge = challengeOf();
        await vi.waitFor(() => expect(retryButton(stage)).toBeDefined());

        retryButton(stage)!.click();

        await vi.waitFor(() =>
            expect(stage.shadowRoot?.textContent).toContain("Network unavailable"),
        );

        expect(spinning(stage)).toBe(false);
        expect(credentialsGet).toHaveBeenCalledOnce();
        retryButton(stage)!.click();
        expect(refresh).toHaveBeenCalledTimes(2);
    });

    it.each(["cancellation", "server rejection"])(
        "refreshes the flow and uses the new device challenge after %s",
        async (failure) => {
            const initialChallenge = challengeOf();

            const freshChallenge = challengeOf({
                deviceChallenges: [{ ...deviceChallenge, challenge: { challenge: "AQ==" } }],
            });

            const get = vi
                .spyOn(FlowsApi.prototype, "flowsExecutorGet")
                .mockResolvedValueOnce(initialChallenge)
                .mockResolvedValueOnce(freshChallenge);

            const solve = vi.spyOn(FlowsApi.prototype, "flowsExecutorSolve").mockResolvedValue(
                challengeOf({
                    responseErrors: {
                        webauthn: [{ code: "invalid", string: "Invalid assertion" }],
                    },
                }),
            );

            if (failure === "cancellation") {
                credentialsGet.mockRejectedValueOnce(new DOMException("denied", "NotAllowedError"));
            }

            const executor = new FlowExecutor();
            executor.flowSlug = "test-webauthn-retry";
            document.body.append(executor);
            mounted.push(executor);

            const currentStage = () =>
                executor.shadowRoot
                    ?.querySelector("ak-stage-authenticator-validate")
                    ?.shadowRoot?.querySelector("ak-stage-authenticator-validate-webauthn");

            await vi.waitFor(() =>
                expect(currentStage() && retryButton(currentStage()!)).toBeDefined(),
            );

            expect(credentialsGet).toHaveBeenCalledOnce();
            credentialsGet.mockReturnValue(new Promise(() => {}));

            const selectionRequests = () =>
                solve.mock.calls.filter(
                    ([request]) => "selectedChallenge" in request.flowChallengeResponseRequest,
                );

            expect(selectionRequests()).toHaveLength(1);

            retryButton(currentStage()!)!.click();
            await vi.waitFor(() => expect(credentialsGet).toHaveBeenCalledTimes(2));

            expect(get).toHaveBeenCalledTimes(2);

            expect(get).toHaveBeenLastCalledWith({
                flowSlug: "test-webauthn-retry",
                query: window.location.search.substring(1),
            });

            expect(credentialsGet.mock.calls[1][0].publicKey.challenge).toEqual(
                Uint8Array.from([1]),
            );

            expect(selectionRequests()).toHaveLength(1);
            expect(retryButton(currentStage()!)).toBeUndefined();
        },
    );

    it("falls back to a generic message for an empty response error", async () => {
        const stage = createStage();

        stage.challenge = challengeOf({
            responseErrors: { webauthn: [{ code: "invalid", string: "" }] },
        });

        await stage.updateComplete;

        expect(stage.shadowRoot?.textContent).toContain("Failed to authenticate");
    });
});
