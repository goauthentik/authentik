/**
 * @file Docusaurus releases plugin.
 *
 * @import { LoadContext, Plugin } from "@docusaurus/types"
 */
import * as fs from "node:fs/promises";
import * as path from "node:path";

import { collectReleaseFiles } from "./utils.mjs";

const RELEASES_FILENAME = "releases.gen.json";

/**
 * @typedef {object} ReleasesPluginOptions
 * @property {string} docsDirectory
 * @property {string} staticDirectory
 */

/**
 * @param {LoadContext} _context
 * @param {ReleasesPluginOptions} options
 * @returns {Promise<Plugin>}
 */
async function releasesPlugin(_context, { docsDirectory, staticDirectory }) {
    if (!staticDirectory) {
        throw new Error("releases-plugin: staticDirectory is required");
    }

    return {
        name: "releases-plugin",
        async loadContent() {
            console.log("🚀 releases-plugin loaded");

            const releases = collectReleaseFiles(docsDirectory).map((release) => release.name);

            const outputPath = path.join(staticDirectory, RELEASES_FILENAME);

            await fs.mkdir(path.dirname(outputPath), { recursive: true });
            await fs.writeFile(outputPath, JSON.stringify(releases, null, 2), "utf-8");

            console.log(`✅ ${RELEASES_FILENAME} generated`);
        },
    };
}

export default releasesPlugin;
