/**
 * @file Rehype plugins for the build-time markdown pipeline.
 */

import { CurrentReleaseDocsURL } from "@goauthentik/core/version/node";

import { SKIP, visit } from "unist-util-visit";

/**
 * Resolve a relative `href` against the docs base URL. Same logic the old
 * runtime `MDXAnchor` used: take a `./...` href relative to the file's
 * `publicDirectory`, drop trailing `index`/`.md`/`.mdx`, and absolutize
 * against {@linkcode CurrentReleaseDocsURL}.
 *
 * @param {string} href
 * @param {string} publicDirectory
 * @returns {string}
 */
function resolveDocsHref(href, publicDirectory) {
    // `new URL(...)` against `file:///` lets us reuse the browser-style
    // path resolver while preserving the hash and any query string.
    const joined = `${publicDirectory}/${href}`.replace(/\/{2,}/g, "/");
    const placeholder = new URL(joined, "file:///");
    const next = new URL(placeholder.pathname, CurrentReleaseDocsURL);
    next.pathname = next.pathname.replace(/(index)?\.mdx?$/, "");
    next.search = placeholder.search;
    next.hash = placeholder.hash;
    return next.toString();
}

/**
 * Rehype plugin: resolve relative anchors at build time and wrap every
 * `<a>` in an `<ak-md-a>` light-DOM custom element. The wrapper attaches
 * the fragment-link click interceptor at runtime so clicks on
 * `<a href="#section">` scroll within the host shadow tree rather than
 * overwriting `location.hash` (which would yank the hash-routed SPA off
 * its current page).
 *
 * Wrapping (rather than replacing) keeps the real `<a>` element inside
 * `<ak-mdx>`'s shadow tree where the existing PatternFly link CSS in
 * `styles.css` applies. The wrapper itself uses `display: contents` so
 * it does not perturb inline-flow layout.
 *
 * @param {{ publicDirectory: string }} options
 */
export function rehypeAnchors({ publicDirectory }) {
    return (/** @type {import('hast').Root} */ tree) => {
        visit(tree, "element", (node) => {
            if (node.tagName !== "a") return;

            const props = node.properties || (node.properties = {});
            const href = typeof props.href === "string" ? props.href : "";

            if (!href) return;

            if (href.startsWith(".")) {
                props.href = resolveDocsHref(href, publicDirectory);
                props.target = "_blank";
                props.rel = "noopener noreferrer";
            } else if (!href.startsWith("#")) {
                // Already-absolute external link: open in a new tab.
                props.target = "_blank";
                props.rel = "noopener noreferrer";
            }

            // Wrap the anchor in `<ak-md-a>` by mutating the node in
            // place: the `<a>`'s contents become a single child, the
            // outer node becomes the wrapper. Returning `SKIP` keeps
            // the visitor from descending into the freshly-stamped
            // child anchor (which would re-match this filter and
            // recurse forever).
            /** @type {import('hast').Element} */
            const original = {
                type: "element",
                tagName: "a",
                properties: { ...props },
                children: node.children,
            };

            node.tagName = "ak-md-a";
            node.properties = {};
            node.children = [original];

            return SKIP;
        });
    };
}

/**
 * Rehype plugin: replace `language-mermaid` code blocks with
 * `<ak-diagram>` elements carrying the mermaid source as text content.
 * `<ak-diagram>` reads its own `textContent` and renders the SVG, so no
 * wrapper element is needed.
 */
export function rehypeMermaid() {
    return (/** @type {import('hast').Root} */ tree) => {
        visit(tree, "element", (node) => {
            if (node.tagName !== "pre") return;
            const child = node.children?.[0];
            if (!child || child.type !== "element" || child.tagName !== "code") return;

            const className = child.properties?.className ?? [];
            const classes = Array.isArray(className) ? className : [className];
            if (!classes.includes("language-mermaid")) return;

            const source = (child.children ?? [])
                .map((c) => (c.type === "text" ? c.value : ""))
                .join("");

            node.tagName = "ak-diagram";
            node.properties = {};
            node.children = [{ type: "text", value: source }];

            return SKIP;
        });
    };
}
