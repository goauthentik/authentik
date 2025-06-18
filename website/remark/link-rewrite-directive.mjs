/**
 * @import { Root } from "mdast";
 */
import { visit } from "unist-util-visit";

/**
 * Remark plugin to transform relative links to docs to absolute URLs
 * @param {Map<string, string>} rewriteMap Map of urls to rewrite where the key is the prefix to check for and the value is the domain to add
 */
function remarkLinkRewrite(rewriteMap) {
    return () => {
        /**
         * @param {Root} tree The MDAST tree to transform.
         */
        return async (tree) => {
            visit(tree, (node) => {
                if (node.type !== "link") {
                    return;
                }
                rewriteMap.forEach((v, k) => {
                    if (!node.url.startsWith(k)) {
                        return;
                    }
                    node.url = `${v}${node.url}`;
                });
            });
        };
    };
}

export default remarkLinkRewrite;
