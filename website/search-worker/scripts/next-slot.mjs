/**
 * @file Prints the slot a rebuild should write: the one the hosted index does not serve.
 *   Reads the JSON that `wrangler d1 execute DB --remote --json --command "SELECT slot FROM
 *   search_current"` prints, on standard input. Before the first import the table does not
 *   exist, the command fails, and the slot is `a`.
 */

import { readFileSync } from "node:fs";

import { INDEX_SLOTS, nextSlot } from "@goauthentik/docusaurus-theme/search/common";

let current = null;

try {
    const output = /** @type {{ results?: { slot?: unknown }[] }[]} */ (
        JSON.parse(readFileSync(0, "utf-8"))
    );
    const slot = output[0]?.results?.[0]?.slot;

    if (typeof slot === "string" && INDEX_SLOTS.includes(/** @type {never} */ (slot))) {
        current = /** @type {import("@goauthentik/docusaurus-theme/search/common").IndexSlot} */ (
            slot
        );
    }
} catch {
    current = null;
}

process.stdout.write(current === null ? INDEX_SLOTS[0] : nextSlot(current));
