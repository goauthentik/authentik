import GithubSlugger from "github-slugger";
import { Heading, Root } from "mdast";
import { toString } from "mdast-util-to-string";
import { Plugin } from "unified";
import { visit } from "unist-util-visit";
import { VFile } from "vfile";

/**
 * Remark plugin to add IDs to headings.
 *
 * Uses `github-slugger` to match the anchor IDs Docusaurus generates for the
 * same content, so intra-page links resolve identically in-app and on the docs
 * site (e.g. `## About OAuth 2.0 and OIDC` → `about-oauth-20-and-oidc`, not
 * `about-oauth-2-0-and-oidc`).
 */
export const remarkHeadings: Plugin<[], Root, VFile> = () => {
    return function transformer(tree) {
        const slugger = new GithubSlugger();
        const visitor = (node: Heading) => {
            const textContent = toString(node);
            const id = slugger.slug(textContent);

            node.data = node.data || {};
            node.data.hProperties = {
                ...node.data.hProperties,
                id,
            };
        };

        visit(tree, "heading", visitor);
    };
};
