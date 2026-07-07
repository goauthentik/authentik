import { truncateString } from "../src/string.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("truncateString", () => {
    it("returns the input unchanged when it fits", () => {
        expect(truncateString("hello", cc(10))).toBe("hello");
    });

    it("uses end-ellipsis by default", () => {
        expect(truncateString("hello world", cc(8))).toBe("hello w…");
    });

    it("uses middle-ellipsis when mode is middle", () => {
        expect(truncateString("abcdefghij", { maxWidth: 7, mode: "middle" })).toBe("abc…hij");
    });
});
