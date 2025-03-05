/**
 * @import {Plugin} from 'unified'
 * @import {Directives} from 'mdast-util-directive'
 * @import {} from 'mdast-util-to-hast'
 * @import {Root} from 'mdast'
 * @import {VFile} from 'vfile'
 */
import { h } from "hastscript";
import { visit } from "unist-util-visit";

const ADMONITION_TYPES = new Set(["info", "warning", "danger", "note"]);

/**
 * Remark plugin to process links
 * @type {Plugin<[unknown], Root, VFile>}
 */
export function remarkAdmonition() {
    return function transformer(tree) {
        /**
         * @param {Directives} node
         */
        const visitor = (node) => {
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
}
