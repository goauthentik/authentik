import "#flow/stages/authenticator_validate/AuthenticatorValidateStage";
import type { AuthenticatorValidateStage } from "#flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { StageHost } from "#flow/types";

import {
    AuthenticatorValidationChallenge,
    DeviceChallenge,
    DeviceClassesEnum,
} from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/* spellchecker:ignore unstub */

function webauthnChallengeOf(nonce: string): DeviceChallenge {
    return {
        deviceClass: DeviceClassesEnum.Webauthn,
        deviceUid: "1",
        challenge: { challenge: nonce, allowCredentials: [] },
        lastUsed: new Date(),
    };
}

function emailChallengeOf(): DeviceChallenge {
    return {
        deviceClass: DeviceClassesEnum.Email,
        deviceUid: "2",
        challenge: { email: "a***@goauthentik.io" },
        lastUsed: new Date(),
    };
}

function challengeOf(
    deviceChallenges: DeviceChallenge[],
    overrides: Partial<AuthenticatorValidationChallenge> = {},
): AuthenticatorValidationChallenge {
    return {
        component: "ak-stage-authenticator-validate",
        pendingUser: "akadmin",
        pendingUserAvatar: "",
        deviceChallenges,
        configurationStages: [],
        ...overrides,
    };
}

/**
 * A minimal stand-in for the credential an authenticator would hand back.
 *
 * See `AuthenticatorValidateStageWebAuthn.browser.test.ts`.
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
let credentialsGet: ReturnType<typeof vi.fn>;
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
    submit = vi.fn().mockResolvedValue(true);
    credentialsGet = vi.fn().mockResolvedValue(assertionOf());

    fetchMock = vi
        .fn()
        .mockResolvedValue(
            new Response(JSON.stringify({}), { headers: { "Content-Type": "application/json" } }),
        );

    vi.stubGlobal("navigator", {
        ...navigator,
        credentials: { get: credentialsGet },
    });

    vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
    vi.unstubAllGlobals();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

function createStage(): AuthenticatorValidateStage {
    const stage = document.createElement("ak-stage-authenticator-validate");

    stage.host = { submit, flowSlug: "default-authentication-flow" } as unknown as StageHost;

    document.body.append(stage);
    mounted.push(stage);

    return stage;
}

const webauthnStage = (stage: HTMLElement) =>
    stage.shadowRoot?.querySelector("ak-stage-authenticator-validate-webauthn");

const retryButton = (stage: HTMLElement) =>
    Array.from(webauthnStage(stage)?.shadowRoot?.querySelectorAll("button") ?? []).find((button) =>
        button.textContent?.includes("Retry authentication"),
    );

const requestedChallenge = (call: number) =>
    Array.from(new Uint8Array(credentialsGet.mock.calls[call][0].publicKey.challenge));

describe("AuthenticatorValidateStage", () => {
    it("answers the latest challenge when the backend issues a new one for the selected device", async () => {
        const stage = createStage();

        stage.challenge = challengeOf([webauthnChallengeOf("AQID")]);

        await vi.waitFor(() => expect(submit).toHaveBeenCalledOnce());
        expect(requestedChallenge(0)).toEqual([1, 2, 3]);

        // The backend rejected the response and re-rendered the stage with a new challenge
        stage.challenge = challengeOf([webauthnChallengeOf("BAUG")], {
            responseErrors: { webauthn: [{ code: "invalid", string: "Assertion failed" }] },
        });

        await vi.waitFor(() => expect(retryButton(stage)).toBeDefined());
        retryButton(stage)!.click();

        await vi.waitFor(() => expect(credentialsGet).toHaveBeenCalledTimes(2));
        expect(requestedChallenge(1)).toEqual([4, 5, 6]);
    });

    it("does not notify the backend when a WebAuthn challenge is selected", async () => {
        const stage = createStage();

        stage.challenge = challengeOf([webauthnChallengeOf("AQID")]);

        await vi.waitFor(() => expect(submit).toHaveBeenCalledOnce());

        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("waits for the selection notification before submitting a response", async () => {
        let resolveNotification!: (response: Response) => void;

        fetchMock.mockReturnValue(
            new Promise<Response>((resolve) => {
                resolveNotification = resolve;
            }),
        );

        const stage = createStage();

        stage.challenge = challengeOf([emailChallengeOf()]);

        await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());

        const submitted = stage.submit({ component: "ak-stage-authenticator-validate", code: "1" });
        await stage.updateComplete;

        expect(submit).not.toHaveBeenCalled();

        resolveNotification(
            new Response(JSON.stringify({}), { headers: { "Content-Type": "application/json" } }),
        );

        await submitted;

        expect(submit).toHaveBeenCalledOnce();
    });
});
