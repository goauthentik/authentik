import { kebabCase } from "change-case";
import { Heading, Root } from "mdast";
import { toString } from "mdast-util-to-string";
import { Plugin } from "unified";
import { visit } from "unist-util-visit";
import { VFile } from "vfile";

/**
 * Remark plugin to add IDs to headings.
 */
export const remarkHeadings: Plugin<[unknown], Root, VFile> = () => {
    return function transformer(tree) {
        const visitor = (node: Heading) => {
            const textContent = toString(node);
            const id = kebabCase(textContent);

            node.data = node.data || {};
            node.data.hProperties = {
                ...node.data.hProperties,
                id,
            };
        };

        visit(tree, "heading", visitor);
    };
};
