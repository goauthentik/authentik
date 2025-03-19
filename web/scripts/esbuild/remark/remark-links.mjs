/**
 * @import {Plugin} from 'unified'
 * @import {} from 'mdast-util-directive'
 * @import {} from 'mdast-util-to-hast'
 * @import {Root, Link} from 'mdast'
 * @import {VFile} from 'vfile'
 */
import * as path from "node:path";
import { visit } from "unist-util-visit";

const DOCS_DOMAIN = "https://goauthentik.io";

/**
 * Remark plugin to process links
 * @type {Plugin<[unknown], Root, VFile>}
 */
export const remarkLinks = () => {
    return function transformer(tree, file) {
        const docsRoot = path.resolve(file.cwd, "..", "website");

        /**
         * @param {Link} node
         */
        const visitor = (node) => {
            node.data = node.data || {};

            if (node.url.startsWith("#")) {
                node.data.hProperties = {
                    className: "markdown-heading",
                };

                return;
            }

            node.data.hProperties = {
                ...node.data.hProperties,
                rel: "noopener noreferrer",
                target: "_blank",
            };

            if (node.url.startsWith(".") && file.dirname) {
                const nextPathname = path.resolve(
                    "/",
                    path.relative(docsRoot, file.dirname),
                    node.url,
                );
                const nextURL = new URL(nextPathname, DOCS_DOMAIN);

                // Remove trailing .md and .mdx, and trailing "index".
                nextURL.pathname = nextURL.pathname.replace(/(index)?\.mdx?$/, "");

                node.data.hProperties.href = nextURL.toString();
            }
        };

        // @ts-ignore - visit cannot infer the type of the visitor.
        visit(tree, "link", visitor);
    };
};
