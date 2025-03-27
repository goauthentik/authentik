/// <reference types="mdast-util-to-hast" />
/// <reference types="mdast-util-directive" />
import { h } from "hastscript";
import { Root } from "mdast";
import { SKIP, visit } from "unist-util-visit";

/**
 * MDAST plugin to transform `ak-preview` directives into preview badges.
 */
function remarkPreviewDirective() {
    return (tree: Root) => {
        visit(tree, "textDirective", (node) => {
            if (node.name !== "ak-preview") return SKIP;

            const data = node.data || (node.data = {});

            const hast = h("span", {
                ...node.attributes,
                "className": "badge badge--preview",
                "title": `This feature is in preview and may change in the future.`,
                "aria-description": "Preview badge",
                "role": "img",
            });

            data.hName = hast.tagName;
            data.hProperties = hast.properties;

            data.hChildren = [
                {
                    type: "text",
                    value: "Preview",
                },
            ];

            node.children = [];

            return SKIP;
        });
    };
}

export default remarkPreviewDirective;
