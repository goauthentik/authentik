#!/usr/bin/env node
/**
 * @file Builds the combined search index from the command line, without a Docusaurus build.
 *   `pnpm run build:search` from `website/` writes `build/search/search-index.db.gz` with every
 *   URL absolute, and stages the browser runtime beside it. `--site <id>` stores that site's URLs
 *   relative, as its own build does. `--out <dir>` changes the output directory.
 */

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { SEARCH_DIRECTORY } from "./common.mjs";
import { buildSearchIndex, describeBuild } from "./node.mjs";
import { assertSearchSite, loadSearchSites } from "./sites.mjs";

const websiteDir = fileURLToPath(new URL("../..", import.meta.url));

const { values } = parseArgs({
    options: {
        site: { type: "string" },
        out: { type: "string", default: resolve(websiteDir, "build", SEARCH_DIRECTORY) },
    },
});

if (values.site) {
    assertSearchSite(values.site);
}

const report = buildSearchIndex({
    websiteDir,
    sites: loadSearchSites(websiteDir),
    currentSite: values.site,
    outputDir: resolve(values.out),
    onFallback(filePath, error) {
        console.warn(
            `search: read ${filePath} as plain Markdown: ${error instanceof Error ? error.message : String(error)}`,
        );
    },
});

console.log(`search: ${describeBuild(report)}`);
console.log(`search: wrote ${report.indexPath}${report.changed ? "" : " (unchanged)"}`);
