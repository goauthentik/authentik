/**
 * @file Build-time markdown → HTML pipeline.
 *
 * The output is wrapped in a `<div class="pf-c-content" part="content">`
 * envelope so consuming `<ak-mdx>` elements can rely on PatternFly content
 * styles and expose CSS parts (`title`, `content`) to host pages.
 */

import { rehypeAnchors, rehypeMermaid } from "./rehype.ts";
import {
    normalizeAdmonitionLabels,
    remarkAdmonition,
    remarkHeadings,
    remarkLists,
} from "./remark.ts";

import GithubSlugger from "github-slugger";
import type { Element, Root } from "hast";
import { toHtml } from "hast-util-to-html";
import apacheGrammar from "highlight.js/lib/languages/apache";
import diffGrammar from "highlight.js/lib/languages/diff";
import confGrammar from "highlight.js/lib/languages/ini";
import nginxGrammar from "highlight.js/lib/languages/nginx";
import { common } from "lowlight";
import rehypeHighlight from "rehype-highlight";
import remarkDirective from "remark-directive";
import remarkFrontmatter from "remark-frontmatter";
import remarkGFM from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";
import { parse as parseYAML } from "yaml";

/**
 * Pull a YAML frontmatter block off the top of `source` and return both
 * pieces. Returns an empty object if there is no frontmatter.
 */
function splitFrontmatter(source: string): {
    body: string;
    frontmatter: Record<string, unknown>;
} {
    const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
    if (!match) return { body: source, frontmatter: {} };
    const frontmatter = parseYAML(match[1]) || {};
    return { body: source.slice(match[0].length), frontmatter };
}

/**
 * Build the wrapping `<div class="pf-c-content" part="content">` envelope
 * with an optional `<h1 part="title">` prefix, then serialize the whole
 * tree through `hast-util-to-html`. One serializer means one set of
 * escaping rules — no hand-rolled `&`/`<`/`>`/`"` replacement that has
 * to be remembered and audited separately.
 *
 * @param bodyChildren Hast nodes from the markdown pipeline.
 * @param title Frontmatter title, or `null` to omit the `<h1>`.
 */
function renderEnvelope(bodyChildren: Element[], title: string | null): string {
    const children: Element["children"] = [];

    if (title) {
        children.push({
            type: "element",
            tagName: "h1",
            properties: { part: "title" },
            children: [{ type: "text", value: title }],
        });
    }

    children.push(...bodyChildren);

    const root: Root = {
        type: "root",
        children: [
            {
                type: "element",
                tagName: "div",
                properties: { className: ["pf-c-content"], part: "content" },
                children,
            },
        ],
    };

    return toHtml(root);
}

/**
 * Compile a markdown source string to a wrapped HTML string and parsed
 * frontmatter. Used by the build-time plugin; the runtime side mirrors
 * this pipeline in the browser for admin-supplied prose.
 *
 * @param source The markdown source.
 * @param publicDirectory Path of the file's directory inside the docs site,
 *     used to resolve relative `<a>` hrefs at build time.
 */
export async function compileMarkdown(
    source: string,
    publicDirectory: string,
): Promise<{ html: string; frontmatter: Record<string, unknown> }> {
    const { body: rawBody, frontmatter } = splitFrontmatter(source);
    const body = normalizeAdmonitionLabels(rawBody);
    const slugger = new GithubSlugger();

    // Run the pipeline up to (but not including) HTML stringification —
    // we want the hast tree so we can splice it into the envelope and
    // serialize the whole thing in one pass below.
    const processor = unified()
        .use(remarkParse)
        .use(remarkGFM)
        .use(remarkFrontmatter, ["yaml"])
        .use(remarkDirective)
        .use(remarkAdmonition)
        .use(remarkHeadings, { slugger })
        .use(remarkLists)
        .use(remarkRehype, { allowDangerousHtml: false })
        .use(rehypeAnchors, { publicDirectory })
        .use(rehypeHighlight, {
            languages: {
                ...common,
                nginx: nginxGrammar,
                apache: apacheGrammar,
                conf: confGrammar,
                diff: diffGrammar,
            },
        })
        .use(rehypeMermaid);

    const tree = (await processor.run(processor.parse(body), body)) as Root;

    const title = typeof frontmatter.title === "string" ? frontmatter.title : null;
    const html = renderEnvelope(tree.children as Element[], title);

    return { html, frontmatter };
}
