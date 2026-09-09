import { UnwrapSet } from "#common/sets";

import { h } from "hastscript";
import type { Paragraph, Root } from "mdast";
import type { Directives } from "mdast-util-directive";
import type { Plugin } from "unified";
import { visit } from "unist-util-visit";
import type { VFile } from "vfile";

export const ADMONITION_TYPES = new Set([
    "info",
    "warning",
    "danger",
    "note",
    "caution",
    "tip",
] as const);

export type AdmonitionType = UnwrapSet<typeof ADMONITION_TYPES>;

export function isAdmonitionType(value: string): value is AdmonitionType {
    return ADMONITION_TYPES.has(value as AdmonitionType);
}

/**
 * `caution` and `tip` are not first-class PatternFly alert levels — map
 * them to the closest equivalent so PFAlert styles render correctly.
 */
const ADMONITION_LEVEL = {
    info: "pf-m-info",
    warning: "pf-m-warning",
    danger: "pf-m-danger",
    note: "pf-m-info",
    caution: "pf-m-warning",
    tip: "pf-m-success",
} as const satisfies Record<AdmonitionType, string>;

/**
 * Remark plugin to convert `:::info` / `:::warning` / etc. directives
 * to `<ak-alert>` elements. The first child paragraph carrying the
 * `directiveLabel` flag (i.e. `:::info[Title]` syntax) is promoted to
 * a `<strong>` so the title renders inside the admonition slot.
 */
export const remarkAdmonition: Plugin<[], Root, VFile> = () => {
    return function transformer(tree) {
        const visitor = (node: Directives) => {
            if (
                node.type !== "containerDirective" &&
                node.type !== "leafDirective" &&
                node.type !== "textDirective"
            ) {
                return;
            }

            if (!isAdmonitionType(node.name)) return;

            const data = node.data || (node.data = {});
            const tagName = node.type === "textDirective" ? "span" : "ak-alert";
            data.hName = tagName;

            const element = h(tagName, node.attributes || {});
            data.hProperties = element.properties || {};
            data.hProperties.level = ADMONITION_LEVEL[node.name] ?? `pf-m-${node.name}`;

            const children = node.children as Paragraph[];
            const labelIndex = children.findIndex(
                (c) => c.type === "paragraph" && c.data?.directiveLabel,
            );
            if (labelIndex !== -1) {
                const label = children[labelIndex];
                children[labelIndex] = {
                    type: "paragraph",
                    children: [{ type: "strong", children: label.children }],
                };
            }
        };

        // @ts-expect-error visit cannot infer the type of the visitor.
        visit(tree, visitor);
    };
};

/**
 * Match a Docusaurus-style admonition opening line:
 *
 * ```
 *     :::info Title
 *```
 * `remark-directive` only understands the spec form `:::name[label]{attrs}`,
 * so a bare-space label silently falls through as plain text. Rewrite
 * the source so the directive parser sees the bracketed form.
 */
const ADMONITION_BARE_LABEL_RE = new RegExp(
    `^(:::(?:${[...ADMONITION_TYPES].join("|")}))[ \\t]+(.+?)[ \\t]*$`,
    "gm",
);

export function normalizeAdmonitionLabels(source: string): string {
    return source.replace(ADMONITION_BARE_LABEL_RE, "$1[$2]");
}
