/**
 * @file Remark plugins for the build-time markdown pipeline.
 *
 * The runtime side (`src/elements/ak-mdx/remark/*`) mirrors a subset of
 * these. Keeping the shapes parallel makes it easier to spot drift when
 * either pipeline grows a new transform.
 */

import type GithubSlugger from "github-slugger";
import type { Root } from "mdast";
import { visit } from "unist-util-visit";

const ADMONITIONS = new Set(["info", "warning", "danger", "note", "caution", "tip"]);

/**
 * `caution` and `tip` aren't first-class PatternFly alert levels — map
 * them onto the closest equivalent so PFAlert styles render correctly.
 */
const ADMONITION_LEVEL: Record<string, string> = {
    info: "pf-m-info",
    warning: "pf-m-warning",
    danger: "pf-m-danger",
    note: "pf-m-info",
    caution: "pf-m-warning",
    tip: "pf-m-success",
};

/**
 * Match a Docusaurus-style admonition opening line:
 *
 *     :::caution Reserved application slugs
 *
 * `remark-directive` only understands the spec form `:::name[label]{attrs}`
 * — a bare-space label silently falls through as plain text. We rewrite
 * the source so the directive parser sees the bracketed form and the
 * label is preserved as the directive's first paragraph.
 */
const ADMONITION_BARE_LABEL_RE = new RegExp(
    `^(:::(?:${[...ADMONITIONS].join("|")}))[ \\t]+(.+?)[ \\t]*$`,
    "gm",
);

export function normalizeAdmonitionLabels(source: string): string {
    return source.replace(ADMONITION_BARE_LABEL_RE, "$1[$2]");
}

/**
 * Remark plugin: convert `:::info` / `:::warning` / `:::danger` / `:::note`
 * directives into `<ak-alert>` elements with a level attribute. The first
 * child paragraph carrying the `directiveLabel` flag (i.e. `:::info[Title]`
 * syntax) is promoted to a `<strong>` so the title renders as a heading-ish
 * element inside the slot.
 */
export function remarkAdmonition() {
    return (tree: Root) => {
        visit(tree, (node) => {
            if (
                node.type !== "containerDirective" &&
                node.type !== "leafDirective" &&
                node.type !== "textDirective"
            ) {
                return;
            }
            if (!ADMONITIONS.has(node.name)) return;

            const tagName = node.type === "textDirective" ? "span" : "ak-alert";
            const data = node.data || (node.data = {});
            data.hName = tagName;
            data.hProperties = {
                ...(data.hProperties || {}),
                ...(node.attributes || {}),
                level: ADMONITION_LEVEL[node.name] ?? `pf-m-${node.name}`,
            };

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const children = (node.children || []) as any[];
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
        });
    };
}

export interface RemarkHeadingsOptions {
    slugger: GithubSlugger;
}

/**
 * Remark plugin: heading slugs into `id` attributes.
 *
 * Uses `github-slugger` to match the anchor IDs Docusaurus generates for the
 * same content.
 */
export function remarkHeadings({ slugger }: RemarkHeadingsOptions) {
    const flatten = (n: { value?: string; children?: unknown[] }): string => {
        if (n.value) return n.value;
        if (n.children) return n.children.map((child) => flatten(child as typeof n)).join("");
        return "";
    };

    return (tree: Root) => {
        visit(tree, "heading", (node) => {
            const id = slugger.slug(flatten(node));
            const data = node.data || (node.data = {});
            data.hProperties = { ...(data.hProperties || {}), id };
        });
    };
}

/**
 * Remark plugin: tag lists with PatternFly's content class.
 */
export function remarkLists() {
    return (tree: Root) => {
        visit(tree, "list", (node) => {
            const data = node.data || (node.data = {});
            data.hProperties = {
                ...(data.hProperties || {}),
                className: "pf-c-list",
            };
        });
    };
}
