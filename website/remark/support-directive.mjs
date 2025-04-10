/**
 * @file Remark plugin to transform `ak-support` directives into support level badges.
 *
 * @import { Root } from "mdast";
 */
import { h } from "hastscript";
import { SKIP, visit } from "unist-util-visit";

/**
 * Support levels for authentik.
 * @typedef {"authentik" | "community" | "vendor" | "deprecated"} SupportLevel
 */

/**
 * Mapping of support levels to badge classes.
 *
 * @satisfies {Record<SupportLevel, string>}
 */
export const SupportLevelToLabel = /** @type {const} */ ({
    authentik: "authentik",
    community: "Community",
    vendor: "Vendor",
    deprecated: "Deprecated",
});

/**
 * Type-predicate to determine if a string is a known support level.
 *
 * @param {string} input The string to check.
 * @return {input is SupportLevel} True if the string is a known support level.
 */
export function isSupportLevel(input) {
    return Object.hasOwn(SupportLevelToLabel, input);
}

/**
 * MDAST plugin to transform `ak-support` directives into preview badges.
 */
function remarkSupportDirective() {
    /**
     * @param {Root} tree The MDAST tree to transform.
     */
    return function (tree) {
        visit(tree, "textDirective", function (node) {
            if (node.name !== "ak-support") return SKIP;

            const firstChild = node.children[0];

            if (firstChild?.type !== "text") return SKIP;

            const level = firstChild.value.trim();

            if (!isSupportLevel(level)) {
                throw new TypeError(`Invalid support level: ${level}`);
            }

            const label = SupportLevelToLabel[level];

            const data = node.data || (node.data = {});

            const hast = h("span", {
                ...node.attributes,
                className: `badge badge--support-${level}`,
                title: `This feature is supported at the ${label} level.`,
                "aria-description": "Support level badge",
                role: "img",
            });

            data.hName = hast.tagName;
            data.hProperties = hast.properties;

            data.hChildren = [
                {
                    type: "text",
                    value: `Support level: ${label}`,
                },
            ];

            node.children = [];

            return SKIP;
        });
    };
}

export default remarkSupportDirective;
