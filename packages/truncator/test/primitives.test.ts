import {
    endEllipsis,
    middleEllipsis,
    reducePipeline,
    segmentEllipsis,
} from "../src/internal/primitives.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

/* spellchecker:ignore longv */

describe("endEllipsis", () => {
    it("returns the input unchanged when it already fits", () => {
        expect(endEllipsis("hello", cc(10))).toBe("hello");
    });

    it("keeps the head and appends the ellipsis when over budget", () => {
        expect(endEllipsis("hello world", cc(8))).toBe("hello w…");
    });

    it("never exceeds the budget", () => {
        const out = endEllipsis("abcdefghij", cc(4));
        expect(out.length).toBeLessThanOrEqual(4);
    });

    it("returns the bare ellipsis when even one char will not fit", () => {
        expect(endEllipsis("abcdef", cc(1))).toBe("…");
    });
});

describe("middleEllipsis", () => {
    it("returns the input unchanged when it already fits", () => {
        expect(middleEllipsis("abcdef", cc(10))).toBe("abcdef");
    });

    it("keeps head and tail around a central ellipsis", () => {
        expect(middleEllipsis("abcdefghij", cc(7))).toBe("abc…hij");
    });

    it("never exceeds the budget", () => {
        const out = middleEllipsis("abcdefghijklmnop", cc(5));
        expect(out.length).toBeLessThanOrEqual(5);
    });

    it("biases the kept characters toward the head when headBias is high", () => {
        const out = middleEllipsis("abcdefghij", cc(6), { headBias: 0.9 });
        expect(out.startsWith("abc")).toBe(true);
    });
});

describe("segmentEllipsis", () => {
    it("returns the joined segments unchanged when they fit", () => {
        expect(segmentEllipsis(["a", "b", "c"], "-", cc(10))).toBe("a-b-c");
    });

    it("drops whole middle segments keeping first and last", () => {
        expect(segmentEllipsis(["1111", "2222", "3333", "4444"], "-", cc(12))).toBe("1111-…-4444");
    });

    it("falls back to character middle-ellipsis when segments cannot be dropped", () => {
        expect(segmentEllipsis(["aaaa", "bbbb"], "-", cc(5))).toBe("aa…bb");
    });
});

describe("reducePipeline", () => {
    it("returns the value unchanged when it already fits", () => {
        const out = reducePipeline("short", cc(10), [() => "REDUCED"]);
        expect(out).toBe("short");
    });

    it("stops at the first reducer that brings it under budget", () => {
        const out = reducePipeline("longlonglong", cc(4), [
            (v) => v.slice(0, 6),
            (v) => v.slice(0, 3),
        ]);
        expect(out).toBe("lon");
    });

    it("returns the last result even if still over budget", () => {
        const out = reducePipeline("longvalue", cc(2), [(v) => v.slice(0, 5)]);
        expect(out).toBe("longv");
    });
});
