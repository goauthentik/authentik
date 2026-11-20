import "#flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { StageHost } from "#flow/types";

import {
    AuthenticatorValidationChallenge,
    DeviceChallenge,
    DeviceClassesEnum,
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
        pendingUser: "",
        pendingUserAvatar: "",
        deviceChallenges: [deviceChallenge],
        configurationStages: [],
        ...overrides,
    };
}

const mounted: HTMLElement[] = [];

let submit: ReturnType<typeof vi.fn>;
let refresh: ReturnType<typeof vi.fn>;
let credentialsGet: ReturnType<typeof vi.fn>;

beforeEach(() => {
    submit = vi.fn().mockResolvedValue(true);
    refresh = vi.fn().mockResolvedValue(true);
    // Never settles: these tests only check that a ceremony starts
    credentialsGet = vi.fn().mockReturnValue(new Promise(() => {}));

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
    const stage = document.createElement("ak-stage-authenticator-validate");

    stage.host = {
        submit,
        refresh,
        flowSlug: "default-authentication-flow",
    } as unknown as StageHost;

    document.body.append(stage);
    mounted.push(stage);

    return stage;
}

const tryAgainButton = (stage: HTMLElement) =>
    Array.from(stage.shadowRoot?.querySelectorAll("button") ?? []).find((button) =>
        button.textContent?.includes("Try again"),
    );

describe("AuthenticatorValidateStage", () => {
    it("offers to load the stage again when the challenge has no devices", async () => {
        const stage = createStage();

        // The backend rejected a response without loading the stage's devices first
        stage.challenge = challengeOf({
            deviceChallenges: [],
            responseErrors: {
                webauthn: [{ code: "invalid", string: "No compatible device class allowed" }],
            },
        });

        await vi.waitFor(() => expect(tryAgainButton(stage)).toBeDefined());

        expect(stage.shadowRoot?.querySelector('[role="alert"]')?.textContent).toContain(
            "This step could not be loaded",
        );

        tryAgainButton(stage)?.click();
        expect(refresh).toHaveBeenCalledOnce();

        // Loading the stage again selects the device and starts a ceremony by itself
        stage.challenge = challengeOf();

        await vi.waitFor(() => expect(credentialsGet).toHaveBeenCalledOnce());
        expect(tryAgainButton(stage)).toBeUndefined();
    });
});
