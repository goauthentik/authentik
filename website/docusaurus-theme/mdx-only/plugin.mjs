/**
 * @file Docusaurus plugin that keeps site content on `.mdx`.
 *
 * All three sites are MDX-only. Docusaurus builds a `.md` page just fine, so the
 * mistake surfaces later as prose that renders differently than the author expected
 * — directives, JSX, and the shared remark plugins all behave differently. Fail the
 * build up front instead, naming the files to rename.
 *
 * @import { LoadContext, Plugin } from "@docusaurus/types"
 */

import { relative, resolve } from "node:path";

import FastGlob from "fast-glob";

const PLUGIN_NAME = "ak-mdx-only-plugin";

/**
 * @typedef {object} AKMDXOnlyPluginOptions
 * @property {string[]} [ignore] Glob patterns to skip — build output, partials, and tests.
 */

/**
 * @param {LoadContext} loadContext
 * @param {AKMDXOnlyPluginOptions} [options]
 * @returns {Plugin<void>}
 */
function akMDXOnlyPlugin({ siteDir }, { ignore = [] } = {}) {
    return {
        name: PLUGIN_NAME,

        async loadContent() {
            const found = await FastGlob("**/*.md", {
                cwd: siteDir,
                onlyFiles: true,
                ignore,
            });

            if (!found.length) return;

            const listing = found
                .sort()
                .map((entry) => `  ${relative(process.cwd(), resolve(siteDir, entry))}`)
                .join("\n");

            throw new Error(
                [
                    `${PLUGIN_NAME}: content must use the .mdx extension, found ${found.length}:`,
                    listing,
                    "Rename each with `git mv <file>.md <file>.mdx`, or prefix it with `_` if it is not a page.",
                ].join("\n"),
            );
        },
    };
}

export default akMDXOnlyPlugin;
