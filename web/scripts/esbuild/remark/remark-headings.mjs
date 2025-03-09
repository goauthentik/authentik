/**
 * @import {Plugin} from 'unified'
 * @import {Root, Heading} from 'mdast'
 * @import {VFile} from 'vfile'
 */
import { kebabCase } from "change-case";
import { toString } from "mdast-util-to-string";
import { visit } from "unist-util-visit";

/**
 * Remark plugin to process links
 * @type {Plugin<[unknown], Root, VFile>}
 */
export const remarkHeadings = () => {
    return function transformer(tree) {
        /**
         * @param {Heading} node
         */
        const visitor = (node) => {
            const textContent = toString(node);
            const id = kebabCase(textContent);

            node.data = node.data || {};
            node.data.hProperties = {
                ...node.data.hProperties,
                id,
            };
        };

        // @ts-ignore - visit cannot infer the type of the visitor.
        visit(tree, "heading", visitor);
    };
};
