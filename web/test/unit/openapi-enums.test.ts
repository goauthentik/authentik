import { openAPIEnumOptions } from "#common/api/enums";

import {
    CompatibilityModeEnum,
    DigestAlgorithmEnum,
    SignatureAlgorithmEnum,
} from "@goauthentik/api";

import { describe, expect, it } from "vitest";

describe("openAPIEnumOptions", () => {
    it("uses enum keys when values are not algorithm URIs", () => {
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

    it("uses generated member names for vendor enums", () => {
        expect(openAPIEnumOptions(CompatibilityModeEnum)).toContainEqual({
            label: "Salesforce",
            value: "sfdc",
        });
    });

    it("derives algorithm labels from URI fragments", () => {
        expect(openAPIEnumOptions(DigestAlgorithmEnum)).toContainEqual({
            label: "SHA256",
            value: DigestAlgorithmEnum.SHA256,
        });
        expect(openAPIEnumOptions(SignatureAlgorithmEnum)).toContainEqual({
            label: "RSA-SHA256",
            value: SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256,
        });
    });
});
