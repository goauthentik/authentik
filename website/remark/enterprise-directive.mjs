/**
 * @file Remark plugin to transform `ak-enterprise` directives into badges.
 *
 * @import { Root } from "mdast";
 */
import { h } from "hastscript";
import { SKIP, visit } from "unist-util-visit";

/**
 * MDAST plugin to transform `ak-enterprise` directives into badges.
 */
function remarkEnterpriseDirective() {
    /**
     * @param {Root} tree The MDAST tree to transform.
     */
    return function (tree) {
        visit(tree, "textDirective", function (node) {
            if (node.name !== "ak-enterprise") return SKIP;

            const data = node.data || (node.data = {});

            const hast = h("span", {
                ...node.attributes,
                "className": "badge badge--primary",
                "title": `This feature is available in the enterprise version of authentik.`,
                "aria-description": "Enterprise badge",
                "role": "img",
            });

            data.hName = hast.tagName;
            data.hProperties = hast.properties;

            data.hChildren = [
                {
                    type: "text",
                    value: "Enterprise",
                },
            ];

            node.children = [];

            return SKIP;
        });
    };
}

export default remarkEnterpriseDirective;
