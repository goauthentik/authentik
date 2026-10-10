import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";
import { StageHost } from "#flow/types";

import { FlowDesignationEnum, IdentificationChallenge } from "@goauthentik/api";

import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

const challenge = {
    userFields: ["email"],
    passwordFields: false,
    flowDesignation: FlowDesignationEnum.Authentication,
    primaryAction: "Log in",
    showSourceLabels: false,
    passkeyChallenge: { challenge: "AA==", allowCredentials: [] },
} as unknown as IdentificationChallenge;

const mounted: HTMLElement[] = [];

beforeAll(async () => {
    // The controller asks for availability when its module loads, so stub it before importing.
    // Answer slower than a frame, as a real browser can.
    vi.spyOn(PublicKeyCredential, "isConditionalMediationAvailable").mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(true), 100)),
    );

    await import("#flow/stages/identification/IdentificationStage");
});

afterEach(() => {
    vi.unstubAllGlobals();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

describe("ak-stage-identification passkey autofill", () => {
    it("starts the conditional request before focusing the identification field", async () => {
        // Safari only offers passkeys in autofill when the request is pending at focus time.
        const order: string[] = [];

        vi.stubGlobal("navigator", {
            ...navigator,
            credentials: {
                get: vi.fn(() => {
                    order.push("request");

                    return new Promise(() => {});
                }),
            },
        });

        const stage = document.createElement("ak-stage-identification") as IdentificationStage;
        stage.host = {} as StageHost;
        stage.challenge = challenge;
        stage.addEventListener("focusin", () => order.push("focus"));

        document.body.append(stage);
        mounted.push(stage);

        await vi.waitFor(() => expect(order).toContain("focus"));
        expect(order).toEqual(["request", "focus"]);
    });
});
