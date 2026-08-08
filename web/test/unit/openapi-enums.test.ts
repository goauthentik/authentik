import { openAPIEnumOptions } from "#common/api/enums";

import { CompatibilityModeEnum, SignatureAlgorithmEnum } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const VALUES = {
    Default: "default",
    DifferentName: "different_value",
    UnknownDefaultOpenApi: "11184809",
} as const;

describe("openAPIEnumOptions", () => {
    it("labels options by their member name", () => {
        expect(openAPIEnumOptions(VALUES)).toEqual([
            { label: "Default", value: "default", default: false },
            { label: "DifferentName", value: "different_value", default: false },
        ]);
    });

    it("marks the given value as the default", () => {
        expect(openAPIEnumOptions(VALUES, "different_value")).toContainEqual({
            label: "DifferentName",
            value: "different_value",
            default: true,
        });
    });

    it("uses generated member names for vendor enums", () => {
        expect(openAPIEnumOptions(CompatibilityModeEnum)).toContainEqual({
            label: "Salesforce",
            value: "sfdc",
            default: false,
        });
    });

    it("derives algorithm labels from URI fragments", () => {
        expect(openAPIEnumOptions(SignatureAlgorithmEnum)).toContainEqual({
            label: "RSA-SHA256",
            value: SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256,
            default: false,
        });
    });
});
