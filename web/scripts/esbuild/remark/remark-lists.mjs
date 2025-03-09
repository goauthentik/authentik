/**
 * @import {Plugin} from 'unified'
 * @import {Root, List} from 'mdast'
 * @import {VFile} from 'vfile'
 */
import { visit } from "unist-util-visit";

/**
 * Remark plugin to process links
 * @type {Plugin<[unknown], Root, VFile>}
 */
export const remarkLists = () => {
    return function transformer(tree) {
        /**
         * @param {List} node
         */
        const visitor = (node) => {
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
