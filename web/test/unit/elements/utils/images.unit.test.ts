import { parseFontAwesomeIcon } from "#elements/utils/images";

import { describe, expect, it } from "vitest";

describe("parseFontAwesomeIcon", () => {
    it("defaults to fa-solid when no family prefix", () => {
        const result = parseFontAwesomeIcon("fa://fa-key");
        expect(result).toEqual({ family: "fa-solid", iconClass: "fa-key" });
    });

    describe("free families", () => {
        it.each([
            ["solid", "fa-solid"],
            ["regular", "fa-regular"],
            ["brands", "fa-brands"],
        ])("parses %s prefix", (prefix, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${prefix}/fa-github`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-github" });
        });

        it.each([
            ["fas", "fa-solid"],
            ["far", "fa-regular"],
            ["fab", "fa-brands"],
        ])("parses short alias %s", (alias, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${alias}/fa-github`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-github" });
        });
    });

    describe("pro families", () => {
        it.each([
            ["light", "fa-light"],
            ["thin", "fa-thin"],
            ["duotone", "fa-duotone"],
        ])("parses %s prefix", (prefix, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${prefix}/fa-coffee`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-coffee" });
        });

        it.each([
            ["fal", "fa-light"],
            ["fat", "fa-thin"],
            ["fad", "fa-duotone"],
        ])("parses short alias %s", (alias, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${alias}/fa-coffee`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-coffee" });
        });
    });

    describe("sharp families", () => {
        it.each([
            ["sharp-solid", "fa-sharp fa-solid"],
            ["sharp-regular", "fa-sharp fa-regular"],
            ["sharp-light", "fa-sharp fa-light"],
            ["sharp-thin", "fa-sharp fa-thin"],
        ])("parses %s prefix into multi-class", (prefix, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${prefix}/fa-check`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-check" });
        });

        it.each([
            ["fass", "fa-sharp fa-solid"],
            ["fasr", "fa-sharp fa-regular"],
            ["fasl", "fa-sharp fa-light"],
            ["fast", "fa-sharp fa-thin"],
        ])("parses short alias %s", (alias, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${alias}/fa-check`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-check" });
        });
    });

    describe("sharp-duotone families", () => {
        it.each([
            ["sharp-duotone-solid", "fa-sharp-duotone fa-solid"],
            ["sharp-duotone-regular", "fa-sharp-duotone fa-regular"],
            ["sharp-duotone-light", "fa-sharp-duotone fa-light"],
            ["sharp-duotone-thin", "fa-sharp-duotone fa-thin"],
        ])("parses %s prefix into multi-class", (prefix, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${prefix}/fa-star`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-star" });
        });

        it.each([
            ["fasds", "fa-sharp-duotone fa-solid"],
            ["fasdr", "fa-sharp-duotone fa-regular"],
            ["fasdl", "fa-sharp-duotone fa-light"],
            ["fasdt", "fa-sharp-duotone fa-thin"],
        ])("parses short alias %s", (alias, expectedFamily) => {
            const result = parseFontAwesomeIcon(`fa://${alias}/fa-star`);
            expect(result).toEqual({ family: expectedFamily, iconClass: "fa-star" });
        });
    });

    it("falls back to fa-solid for unknown prefix", () => {
        const result = parseFontAwesomeIcon("fa://unknown/fa-widget");
        expect(result).toEqual({ family: "fa-solid", iconClass: "fa-widget" });
    });

    it("falls back to fa-question-circle for invalid icon class", () => {
        const result = parseFontAwesomeIcon("fa://INVALID CHARS!");
        expect(result).toEqual({ family: "fa-solid", iconClass: "fa-question-circle" });
    });

    it("falls back to fa-question-circle for invalid icon class with prefix", () => {
        const result = parseFontAwesomeIcon("fa://brands/INVALID!");
        expect(result).toEqual({ family: "fa-brands", iconClass: "fa-question-circle" });
    });

    it("handles prefix case-insensitively", () => {
        const result = parseFontAwesomeIcon("fa://Brands/fa-github");
        expect(result).toEqual({ family: "fa-brands", iconClass: "fa-github" });
    });
});
