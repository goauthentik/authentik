import type { List, Root } from "mdast";
import type { Plugin } from "unified";
import { visit } from "unist-util-visit";
import type { VFile } from "vfile";

/**
 * Remark plugin to process lists.
 */
export const remarkLists: Plugin<[unknown], Root, VFile> = () => {
    return function transformer(tree) {
        const visitor = (node: List) => {
            node.data = node.data || {};

            node.data.hProperties = {
                ...node.data.hProperties,
                className: "pf-c-list",
            };
        };

        // @ts-ignore - visit cannot infer the type of the visitor.
        visit(tree, "list", visitor);
    };
};
