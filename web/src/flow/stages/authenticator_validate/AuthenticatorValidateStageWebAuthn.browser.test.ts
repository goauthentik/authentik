import "#flow/stages/authenticator_validate/AuthenticatorValidateStageWebAuthn";

import { afterEach, describe, expect, it, vi } from "vitest";

interface TestableWebAuthnStage extends HTMLElement {
    authenticating: boolean;
    challenge: object | null;
    deviceChallenge: { challenge: object };
    errorMessage?: string;
    authenticate(): Promise<boolean>;
    tryAuthenticating(): Promise<unknown>;
    updateComplete: Promise<boolean>;
    updated(changedProperties: Map<PropertyKey, unknown>): void;
}

const mounted: HTMLElement[] = [];

function createStage(): TestableWebAuthnStage {
    const stage = document.createElement(
        "ak-stage-authenticator-validate-webauthn",
    ) as unknown as TestableWebAuthnStage;
    document.body.append(stage);
    mounted.push(stage);

    return stage;
}

afterEach(() => {
    for (const element of mounted.splice(0)) element.remove();
});

describe("AuthenticatorValidateStageWebAuthn", () => {
    it("renders as authenticating before the initial challenge update", () => {
        const stage = createStage();
        expect(stage.authenticating).toBe(true);
    });

    it("does not expose retry without an authentication error", async () => {
        const stage = createStage();
        stage.authenticating = false;
        await stage.updateComplete;

        expect(stage.shadowRoot?.textContent).toContain("Authenticating...");
        expect(stage.shadowRoot?.textContent).not.toContain("Retry authentication");
        expect(stage.shadowRoot?.querySelector("ak-empty-state")?.hasAttribute("loading")).toBe(
            true,
        );
    });

    it("remains authenticating after the flow advances successfully", async () => {
        const stage = createStage();
        stage.authenticating = false;
        stage.authenticate = vi.fn().mockResolvedValue(true);
        await stage.tryAuthenticating();
        expect(stage.authenticating).toBe(true);
    });

    it("remains authenticating until a rejected assertion challenge is rendered", async () => {
        const stage = createStage();
        stage.authenticating = false;
        stage.authenticate = vi.fn().mockResolvedValue(false);
        await stage.tryAuthenticating();
        expect(stage.authenticating).toBe(true);
    });

    it("stops authenticating when a new challenge contains response errors", () => {
        const stage = createStage();
        stage.authenticating = true;
        stage.challenge = {
            responseErrors: {
                webauthn: [{ code: "invalid", string: "Invalid assertion" }],
            },
        };
        stage.deviceChallenge = { challenge: { challenge: "AA==" } };
        stage.authenticate = vi.fn().mockResolvedValue(true);
        stage.updated(new Map([["challenge", {}]]));

        expect(stage.authenticating).toBe(false);
        expect(stage.errorMessage).toBe("Invalid assertion");
        expect(stage.authenticate).not.toHaveBeenCalled();
    });

    it("uses a fallback for an empty response error", () => {
        const stage = createStage();
        stage.challenge = {
            responseErrors: {
                webauthn: [{ code: "invalid", string: "" }],
            },
        };
        stage.deviceChallenge = { challenge: { challenge: "AA==" } };
        stage.authenticate = vi.fn().mockResolvedValue(true);
        stage.updated(new Map([["challenge", {}]]));

        expect(stage.authenticating).toBe(false);
        expect(stage.errorMessage).toBe("Failed to authenticate");
    });

    it("starts authentication again when the element receives a new challenge", () => {
        const stage = createStage();
        stage.authenticating = true;
        stage.challenge = {};
        stage.deviceChallenge = { challenge: { challenge: "AA==" } };
        stage.errorMessage = "Previous error";
        stage.authenticate = vi.fn().mockResolvedValue(true);
        stage.updated(new Map([["challenge", {}]]));

        expect(stage.authenticate).toHaveBeenCalledOnce();
        expect(stage.errorMessage).toBeUndefined();
    });
});
