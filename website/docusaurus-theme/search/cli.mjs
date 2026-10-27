#!/usr/bin/env node
/**
 * @file Builds the combined search index from the command line, without a Docusaurus build.
 *   `pnpm run build:search` from `website/` writes `build/search/search-index.db.gz` with every
 *   URL absolute, and stages the browser runtime beside it. `--site <id>` stores that site's URLs
 *   relative, as its own build does. `--out <dir>` changes the output directory. `--d1 <slot>`
 *   writes the SQL script that fills that slot of the hosted index instead, as
 *   `build/search/search-index.<slot>.sql`.
 */

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { INDEX_SLOTS, SEARCH_DIRECTORY } from "./common.mjs";
import { writeD1Script } from "./d1.mjs";
import { buildCommit, buildSearchIndex, collectSearchRecords, describeBuild } from "./node.mjs";
import { assertSearchSite, loadSearchSites } from "./sites.mjs";

const websiteDir = fileURLToPath(new URL("../..", import.meta.url));

const { values } = parseArgs({
    options: {
        site: { type: "string" },
        out: { type: "string", default: resolve(websiteDir, "build", SEARCH_DIRECTORY) },
        d1: { type: "string" },
    },
});

if (values.site) {
    assertSearchSite(values.site);
}

/**
 * @param {string} filePath
 * @param {unknown} error
 */
function onFallback(filePath, error) {
    console.warn(
        `search: read ${filePath} as plain Markdown: ${error instanceof Error ? error.message : String(error)}`,
    );
}

if (values.d1 !== undefined) {
    const slot = /** @type {import("./common.mjs").IndexSlot} */ (values.d1);

    if (!INDEX_SLOTS.includes(slot)) {
        throw new Error(`search: --d1 takes one of ${INDEX_SLOTS.join(", ")}`);
    }

    const collected = collectSearchRecords({
        websiteDir,
        sites: loadSearchSites(websiteDir),
        currentSite: values.site,
        onFallback,
    });

    const output = resolve(values.out, `search-index.${slot}.sql`);
    const written = writeD1Script(collected.records, output, slot, { commit: buildCommit() });

    console.log(
        `search: ${collected.records.length} records into slot ${slot}; ${written.statements} statements, ${(written.bytes / 1024).toFixed(0)} KiB`,
    );
    console.log(`search: wrote ${output}`);
} else {
    const report = buildSearchIndex({
        websiteDir,
        sites: loadSearchSites(websiteDir),
        currentSite: values.site,
        outputDir: resolve(values.out),
        onFallback,
    });

    console.log(`search: ${describeBuild(report)}`);
    console.log(`search: wrote ${report.indexPath}${report.changed ? "" : " (unchanged)"}`);
}
