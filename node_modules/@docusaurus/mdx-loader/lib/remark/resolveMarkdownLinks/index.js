"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@docusaurus/utils");
const HAS_MARKDOWN_EXTENSION = /\.mdx?$/i;
function parseMarkdownLinkURLPath(link) {
    const urlPath = (0, utils_1.parseLocalURLPath)(link);
    // If it's not local, we don't resolve it even if it's a Markdown file
    // Example, we don't resolve https://github.com/project/README.md
    if (!urlPath) {
        return null;
    }
    // Ignore links without a Markdown file extension (ignoring qs/hash)
    if (!HAS_MARKDOWN_EXTENSION.test(urlPath.pathname)) {
        return null;
    }
    return urlPath;
}
/**
 * A remark plugin to extract the h1 heading found in Markdown files
 * This is exposed as "data.contentTitle" to the processed vfile
 * Also gives the ability to strip that content title (used for the blog plugin)
 */
const plugin = function plugin(options) {
    const { resolveMarkdownLink } = options;
    return async (root, file) => {
        const { visit } = await import('unist-util-visit');
        visit(root, ['link', 'definition'], (node) => {
            const link = node;
            const linkURLPath = parseMarkdownLinkURLPath(link.url);
            if (!linkURLPath) {
                return;
            }
            const permalink = resolveMarkdownLink({
                sourceFilePath: file.path,
                linkPathname: linkURLPath.pathname,
            });
            if (permalink) {
                // This reapplies the link ?qs#hash part to the resolved pathname
                const resolvedUrl = (0, utils_1.serializeURLPath)({
                    ...linkURLPath,
                    pathname: permalink,
                });
                link.url = resolvedUrl;
            }
        });
    };
};
exports.default = plugin;
//# sourceMappingURL=index.js.map