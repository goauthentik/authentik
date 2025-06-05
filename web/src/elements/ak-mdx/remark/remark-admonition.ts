import { h } from "hastscript";
import type { Root } from "mdast";
import type { Directives } from "mdast-util-directive";
import type { Plugin } from "unified";
import { visit } from "unist-util-visit";
import type { VFile } from "vfile";

const ADMONITION_TYPES = new Set(["info", "warning", "danger", "note"]);

/**
 * Remark plugin to add admonition classes to directives.
 */
export const remarkAdmonition: Plugin<[unknown], Root, VFile> = () => {
    return function transformer(tree) {
        const visitor = (node: Directives) => {
            if (
                node.type === "containerDirective" ||
                node.type === "leafDirective" ||
                node.type === "textDirective"
            ) {
                if (!ADMONITION_TYPES.has(node.name)) return;

                const data = node.data || (node.data = {});

                const tagName = node.type === "textDirective" ? "span" : "ak-alert";

                data.hName = tagName;

                const element = h(tagName, node.attributes || {});

                data.hProperties = element.properties || {};
                data.hProperties.level = `pf-m-${node.name}`;
            }
        };

        // @ts-ignore - visit cannot infer the type of the visitor.
        visit(tree, visitor);
    };
};
