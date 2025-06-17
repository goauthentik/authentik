/**
 * @import { Root } from "mdast";
 */
import { visit } from "unist-util-visit";

/**
 * Remark plugin to transform relative links to docs to absolute URLs
 */
function remarkIntegrationsLinkRewrite() {
    /**
     * @param {Root} tree The MDAST tree to transform.
     */
    return async (tree) => {
        visit(tree, (node) => {
            if (node.type !== "link") {
                return;
            }
            if (!node.url.startsWith("/docs")) {
                return;
            }
            node.url = `https://docs.goauthentik.io${node.url}`;
        });
    };
}

export default remarkIntegrationsLinkRewrite;
