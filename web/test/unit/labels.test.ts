import { actionToLabel, formatIntentLabel } from "#common/labels";

import { EventActions, IntentEnum } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

describe("actionToLabel", () => {
    it("returns the translated label for a known action", () => {
        expect(actionToLabel(EventActions.Login)).toBe("Login");
    });

    it("returns a prefixed custom action unchanged", () => {
        expect(actionToLabel("custom_example_action")).toBe("custom_example_action");
    });

    it("returns an arbitrary action unchanged", () => {
        expect(actionToLabel("Example Custom Action")).toBe("Example Custom Action");
    });

    it("returns an empty string when the action is missing", () => {
        expect(actionToLabel()).toBe("");
    });
});

describe("formatIntentLabel", () => {
    it.each([
        [IntentEnum.Api, "API Access"],
        [IntentEnum.AppPassword, "App password"],
        [IntentEnum.Recovery, "Recovery"],
        [IntentEnum.Verification, "Verification"],
    ])("labels the %s intent", (intent, expected) => {
        expect(formatIntentLabel(intent)).toBe(expected);
    });

    it("does not throw on an intent missing from the schema", () => {
        expect(() => formatIntentLabel("api-access" as IntentEnum)).not.toThrow();
    });

    it("displays a missing intent by its key", () => {
        expect(formatIntentLabel("api-access" as IntentEnum)).toBe("api-access");
    });

    it("does not throw on a null intent", () => {
        expect(() => formatIntentLabel(null as unknown as IntentEnum)).not.toThrow();
    });
});
