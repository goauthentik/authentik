import { actionToLabel } from "#common/labels";

import { EventActions } from "@goauthentik/api";

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
