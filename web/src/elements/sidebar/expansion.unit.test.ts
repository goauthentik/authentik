import * as SidebarState from "./expansion.js";

import { describe, expect, test } from "vitest";

describe("parseState", () => {
    test("keeps boolean entries", () => {
        expect(SidebarState.parseState({ directory: true, system: false })).toEqual({
            directory: true,
            system: false,
        });
    });

    test("discards a value that is not a record", () => {
        // Storage outlives any given build.
        // A record written by an older version, or edited by hand, must not surface as expansion state.

        for (const value of [null, undefined, "a string", 42, ["directory"]]) {
            expect(SidebarState.parseState(value), `discards ${JSON.stringify(value)}`).toEqual({});
        }
    });

    test("discards non-boolean entries while keeping usable ones", () => {
        expect(SidebarState.parseState({ directory: true, events: "yes", system: null })).toEqual({
            directory: true,
        });
    });
});
