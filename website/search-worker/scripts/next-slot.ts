/**
 * @file Prints the slot a rebuild should write: the one the hosted index does not serve.
 *   It asks D1 for the current slot through wrangler. Before the first import the pointer table
 *   does not exist, and the slot is `a`. Any other failure of the query stops the rebuild, so a
 *   wrong credential never turns into a write over the slot readers are using.
 */

import { spawnSync } from "node:child_process";

import {
    INDEX_SLOTS,
    type IndexSlot,
    nextSlot,
    SLOT_POINTER_TABLE,
} from "@goauthentik/docusaurus-theme/search/common";

export interface CommandResult {
    status: number | null;
    stdout: string;
    stderr: string;
}

/**
 * The rows `wrangler d1 execute --json` prints: one entry per statement.
 */
interface ExecuteOutput {
    results?: { slot?: unknown }[];
}

/**
 * The slot to write, given the result of `SELECT slot FROM search_current`.
 */
export function slotToWrite(result: CommandResult): IndexSlot {
    if (result.status !== 0) {
        if (`${result.stdout}\n${result.stderr}`.includes(`no such table: ${SLOT_POINTER_TABLE}`)) {
            return INDEX_SLOTS[0];
        }

        throw new Error(
            `search: reading the current slot failed with status ${result.status}:\n${result.stderr || result.stdout}`,
        );
    }

    const output = JSON.parse(result.stdout) as ExecuteOutput[];
    const slot = output[0]?.results?.[0]?.slot;

    if (typeof slot !== "string" || !(INDEX_SLOTS as readonly string[]).includes(slot)) {
        throw new Error(`search: the pointer table names no slot: ${result.stdout}`);
    }

    return nextSlot(slot as IndexSlot);
}

if (import.meta.main) {
    const result = spawnSync(
        "wrangler",
        [
            "d1",
            "execute",
            "DB",
            "--remote",
            "--json",
            "--command",
            `SELECT slot FROM ${SLOT_POINTER_TABLE}`,
        ],
        { encoding: "utf-8", shell: process.platform === "win32" },
    );

    process.stdout.write(slotToWrite(result));
}
