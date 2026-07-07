import { characterMeasurer } from "../src/measurer.js";

import { describe, expect, it } from "vitest";

describe("characterMeasurer", () => {
    it("returns the number of code units in the string", () => {
        expect(characterMeasurer("hello")).toBe(5);
    });

    it("returns 0 for the empty string", () => {
        expect(characterMeasurer("")).toBe(0);
    });
});
