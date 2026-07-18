/**
 * @import { Root } from "mdast";
 */

import { SKIP, visit } from "unist-util-visit";

/**
 * @typedef {[pattern: string | RegExp, replacement: string]} Rewrite
 */

/**
 * Remark plugin to transform relative links to docs to absolute URLs
 * @param {Iterable<[string, string]>} rewrites Map of urls to rewrite where the key is the prefix to check for and the value is the domain to add
 */
export function remarkLinkRewrite(rewrites) {
    const map = new Map(rewrites);

    return () => {
        /**
         * @param {Root} tree The MDAST tree to transform.
         */
        return (tree) => {
            visit(tree, "link", (node) => {
                for (const [pattern, replacement] of map) {
                    if (!node.url.startsWith(pattern)) continue;

                    node.url = node.url.replace(pattern, replacement);
                }

                return SKIP;
            });
        };
    };
}

export default remarkLinkRewrite;
