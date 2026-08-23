import { reorderKeys } from "./reorder.js";

import { describe, expect, it } from "vitest";

describe("reorderKeys", () => {
    it("moves a key above the target when dropping on its upper half", () => {
        expect(reorderKeys(["a", "b", "c"], "c", "a", false)).toEqual(["c", "a", "b"]);
    });

    it("moves a key below the target when dropping on its lower half", () => {
        expect(reorderKeys(["a", "b", "c"], "a", "b", true)).toEqual(["b", "a", "c"]);
    });

    it("moves a key from the middle to the end", () => {
        expect(reorderKeys(["a", "b", "c"], "b", "c", true)).toEqual(["a", "c", "b"]);
    });

    it("returns the original order when dropped on itself", () => {
        expect(reorderKeys(["a", "b", "c"], "b", "b", false)).toEqual(["a", "b", "c"]);
    });

    it("returns the original order when there is no target row", () => {
        expect(reorderKeys(["a", "b", "c"], "b", null, false)).toEqual(["a", "b", "c"]);
    });

    it("ignores unknown dragging or target keys", () => {
        expect(reorderKeys(["a", "b", "c"], "z", "a", false)).toEqual(["a", "b", "c"]);
        expect(reorderKeys(["a", "b", "c"], "a", "z", false)).toEqual(["a", "b", "c"]);
    });

    it("does not mutate the input array", () => {
        const input = ["a", "b", "c"];
        reorderKeys(input, "c", "a", false);
        expect(input).toEqual(["a", "b", "c"]);
    });
});
