import assert from "node:assert/strict";
import { test } from "node:test";

import { slotToWrite } from "../scripts/next-slot.ts";

const ok = (slot: string) => ({
    status: 0,
    stdout: JSON.stringify([{ results: [{ slot }], success: true }]),
    stderr: "",
});

test("the other slot is written", () => {
    assert.equal(slotToWrite(ok("a")), "b");
    assert.equal(slotToWrite(ok("b")), "a");
});

test("the first import writes slot a", () => {
    assert.equal(
        slotToWrite({
            status: 1,
            stdout: "",
            stderr: "✘ [ERROR] no such table: search_current: SQLITE_ERROR",
        }),
        "a",
    );
});

test("any other failure stops the rebuild", () => {
    assert.throws(
        () => slotToWrite({ status: 1, stdout: "", stderr: "Authentication error [code: 10000]" }),
        /status 1[\s\S]*Authentication error/,
    );
});

test("a pointer row naming no slot stops the rebuild", () => {
    assert.throws(() => slotToWrite(ok("c")), /names no slot/);
    assert.throws(
        () => slotToWrite({ status: 0, stdout: JSON.stringify([{ results: [] }]), stderr: "" }),
        /names no slot/,
    );
});
