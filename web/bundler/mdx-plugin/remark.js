/**
 * @file Remark plugins for the build-time markdown pipeline.
 *
 * The runtime side (`src/elements/ak-mdx/remark/*`) mirrors a subset of
 * these. Keeping the shapes parallel makes it easier to spot drift when
 * either pipeline grows a new transform.
 */

import { visit } from "unist-util-visit";

const ADMONITIONS = new Set(["info", "warning", "danger", "note", "caution", "tip"]);

/**
 * `caution` and `tip` aren't first-class PatternFly alert levels — map
 * them onto the closest equivalent so PFAlert styles render correctly.
 */
const ADMONITION_LEVEL = {
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

/**
 * @param {string} source
 * @returns {string}
 */
export function normalizeAdmonitionLabels(source) {
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
    return (/** @type {import('mdast').Root} */ tree) => {
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
                level:
                    /** @type {Record<string, string>} */ (ADMONITION_LEVEL)[node.name] ??
                    `pf-m-${node.name}`,
            };

            const children = /** @type {any[]} */ (node.children || []);
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

/**
 * Remark plugin: kebab-case heading slugs into `id` attributes.
 */
export function remarkHeadings() {
    /**
     * @param {{ value?: string, children?: any[] }} n
     * @returns {string}
     */
    const flatten = (n) => {
        if (n.value) return n.value;
        if (n.children) return n.children.map(flatten).join("");
        return "";
    };

    return (/** @type {import('mdast').Root} */ tree) => {
        visit(tree, "heading", (node) => {
            const id = flatten(node)
                .toLowerCase()
                .trim()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/^-+|-+$/g, "");
            const data = node.data || (node.data = {});
            data.hProperties = { ...(data.hProperties || {}), id };
        });
    };
}

/**
 * Remark plugin: tag lists with PatternFly's content class.
 */
export function remarkLists() {
    return (/** @type {import('mdast').Root} */ tree) => {
        visit(tree, "list", (node) => {
            const data = node.data || (node.data = {});
            data.hProperties = {
                ...(data.hProperties || {}),
                className: "pf-c-list",
            };
        });
    };
}
