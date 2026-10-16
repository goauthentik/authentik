import { parseSidebarExpansionState } from "./expansion.js";

import { describe, expect, test } from "vitest";

describe("parseSidebarExpansionState", () => {
    test("keeps boolean entries", () => {
        expect(parseSidebarExpansionState({ directory: true, system: false })).toEqual({
            directory: true,
            system: false,
        });
    });

    test("discards a value that is not a record", () => {
        // Storage outlives any given build.
        // A record written by an older version, or edited by hand, must not surface as expansion state.

        for (const value of [null, undefined, "a string", 42, ["directory"]]) {
            expect(parseSidebarExpansionState(value), `discards ${JSON.stringify(value)}`).toEqual(
                {},
            );
        }
    });

    test("discards non-boolean entries while keeping usable ones", () => {
        expect(
            parseSidebarExpansionState({ directory: true, events: "yes", system: null }),
        ).toEqual({ directory: true });
    });
});
