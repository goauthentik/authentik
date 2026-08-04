import { openAPIEnumOptions } from "#common/api/enums";

import { CompatibilityModeEnum, DigestAlgorithmEnum } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

describe("openAPIEnumOptions", () => {
    it("uses enum keys when no display labels were generated", () => {
        const values = {
            Default: "default",
            DifferentName: "different_value",
        } as const;

        expect(openAPIEnumOptions(values)).toEqual([
            { label: "Default", value: "default" },
            { label: "DifferentName", value: "different_value" },
        ]);
    });

    it("omits the generated unknown value", () => {
        const values = {
            Default: "default",
            UnknownDefaultOpenApi: "11184809",
        } as const;

        expect(openAPIEnumOptions(values)).toEqual([{ label: "Default", value: "default" }]);
    });

    it("uses generated display labels for opted-in enums", () => {
        expect(openAPIEnumOptions(CompatibilityModeEnum)).toContainEqual({
            label: "Salesforce",
            value: "sfdc",
        });
        expect(openAPIEnumOptions(DigestAlgorithmEnum)).toContainEqual({
            label: "SHA256",
            value: DigestAlgorithmEnum.SHA256,
        });
    });
});
