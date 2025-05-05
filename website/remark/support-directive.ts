import { h } from "hastscript";
import { Root } from "mdast";
import "mdast-util-directive";
import "mdast-util-to-hast";
import { coerce } from "semver";
import { SKIP, visit } from "unist-util-visit";

/**
 * Support levels for authentik.
 */
export type SupportLevel = "authentik" | "community" | "vendor" | "deprecated";

/**
 * Mapping of support levels to badge classes.
 */
export const SupportLevelToLabel = {
    authentik: "authentik",
    community: "Community",
    vendor: "Vendor",
    deprecated: "Deprecated",
} as const satisfies Record<SupportLevel, string>;

/**
 * Type-predicate to determine if a string is a known support level.
 */
export function isSupportLevel(input: string): input is SupportLevel {
    return Object.hasOwn(SupportLevelToLabel, input);
}

/**
 * MDAST plugin to transform `ak-support` directives into preview badges.
 */
function remarkSupportDirective() {
    return function (tree: Root) {
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
                "className": `badge badge--support-${level}`,
                "title": `This feature is supported at the ${label} level.`,
                "aria-description": "Support level badge",
                "role": "img",
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
