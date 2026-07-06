import * as truncator from "../src/index.js";

import { describe, expect, it } from "vitest";

describe("package entry", () => {
    it("re-exports every truncator", () => {
        expect(typeof truncator.truncateURL).toBe("function");
        expect(typeof truncator.truncateHash).toBe("function");
        expect(typeof truncator.truncateUUID).toBe("function");
        expect(typeof truncator.truncateMacAddress).toBe("function");
        expect(typeof truncator.truncateIPAddress).toBe("function");
        expect(typeof truncator.truncateEmail).toBe("function");
        expect(typeof truncator.truncateUserAgent).toBe("function");
        expect(typeof truncator.truncateString).toBe("function");
    });

    it("exposes the measurer entry points for DOM callers", () => {
        expect(typeof truncator.characterMeasurer).toBe("function");
        expect(typeof truncator.createCanvasMeasurer).toBe("function");
    });
});
