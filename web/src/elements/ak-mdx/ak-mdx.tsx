import "#elements/Alert";

import { globalAK } from "#common/global";
import { BrandedHTMLPolicy } from "#common/purify";

import { MDXAnchor } from "#elements/ak-mdx/components/MDXAnchor";
import { MDXWrapper } from "#elements/ak-mdx/components/MDXWrapper";
import { fetchMDXModule, MDXModuleContext } from "#elements/ak-mdx/MDXModuleContext";
import { remarkAdmonition } from "#elements/ak-mdx/remark/remark-admonition";
import { remarkHeadings } from "#elements/ak-mdx/remark/remark-headings";
import { remarkLists } from "#elements/ak-mdx/remark/remark-lists";
import Styles from "#elements/ak-mdx/styles.css";
import { AKElement } from "#elements/Base";
import MermaidStyles from "#elements/mermaid/mermaid.css";
import { loadMermaid } from "#elements/mermaid/utils";

import { DistDirectoryName, StaticDirectoryName } from "#paths";
import OneDark from "#styles/atom/one-dark.css";

import { compile as compileMDX, run as runMDX } from "@mdx-js/mdx";
import apacheGrammar from "highlight.js/lib/languages/apache";
import diffGrammar from "highlight.js/lib/languages/diff";
import confGrammar from "highlight.js/lib/languages/ini";
import nginxGrammar from "highlight.js/lib/languages/nginx";
import { common } from "lowlight";
import { createRoot, Root } from "react-dom/client";
import * as runtime from "react/jsx-runtime";
import rehypeHighlight, { Options as HighlightOptions } from "rehype-highlight";
import rehypeMermaid, { RehypeMermaidOptions } from "rehype-mermaid";
import remarkDirective from "remark-directive";
import remarkFrontmatter from "remark-frontmatter";
import remarkGFM from "remark-gfm";
import remarkMdxFrontmatter from "remark-mdx-frontmatter";
import remarkParse from "remark-parse";
import type { MDXModule } from "~docs/types";

import { customElement, property } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";

const highlightThemeOptions: HighlightOptions = {
    languages: {
        ...common,
        nginx: nginxGrammar,
        apache: apacheGrammar,
        conf: confGrammar,
        diff: diffGrammar,
    },
};

/**
 * A replacer function that can be used to modify the output of the MDX component.
 */
export type Replacer = (input: string) => string;

/**
 * The syntax a source is compiled as.
 *
 * - `mdx` additionally parses JSX, expressions (`{...}`) and ESM
 *   imports/exports, all of which are evaluated when the compiled module runs.
 * - `md` is CommonMark only, i.e. no part of the source is evaluated.
 *
 * @see {@linkcode https://mdxjs.com/packages/mdx/#optionsformat}
 */
type ContentFormat = "md" | "mdx";

@customElement("ak-mdx")
export class AKMDX extends AKElement {
    // HACK: Fixes Lit Analyzer's parsing of TSX files with decorators.

    @((property as typeof property)({ type: String, reflect: true }))
    public url?: string;

    @((property as typeof property)())
    public content?: string;

    @((property as typeof property)({ attribute: false }))
    public replacers: Replacer[] = [];

    #reactRoot: Root | null = null;

    static styles = [
        // ---

        PFList,
        PFTable,
        PFContent,
        OneDark,
        MermaidStyles,
        Styles,
    ];

    public async connectedCallback() {
        super.connectedCallback();
        this.#reactRoot = createRoot(this.shadowRoot!);

        let nextMDXModule: MDXModule | undefined;
        const { relBase } = globalAK().api;

        if (this.url) {
            const pathname =
                relBase +
                StaticDirectoryName +
                "/" +
                DistDirectoryName +
                this.url.slice(this.url.indexOf("/assets"));

            nextMDXModule = await fetchMDXModule(pathname);

            // Documentation is authored in-tree and bundled with the web
            // interface, so it may use the full MDX syntax.
            return this.delegateRender(nextMDXModule, "mdx");
        }

        nextMDXModule = {
            content: `${BrandedHTMLPolicy.createHTML(this.content || "")}`,
        };

        // `content` is supplied through the API — user and group notes, and
        // blueprint descriptions — and is therefore compiled as CommonMark, so
        // that no part of it is evaluated at runtime.
        return this.delegateRender(nextMDXModule, "md");
    }

    protected async delegateRender(
        mdxModule: MDXModule,
        format: ContentFormat = "mdx",
    ): Promise<void> {
        if (!this.#reactRoot) return;

        const normalized = this.replacers.reduce(
            (content, replacer) => replacer(content),
            mdxModule.content,
        );

        const { activeTheme } = this;

        const mdx = await compileMDX(normalized, {
            format,
            outputFormat: "function-body",
            remarkPlugins: [
                remarkParse,
                remarkDirective,
                remarkAdmonition,
                remarkGFM,
                remarkFrontmatter,
                remarkMdxFrontmatter,
                remarkHeadings,
                remarkLists,
            ],
            rehypePlugins: [
                // ---
                [rehypeHighlight, highlightThemeOptions],
                [
                    rehypeMermaid,
                    {
                        prefix: "mermaid-svg-",
                        colorScheme: activeTheme,
                        mermaidConfig: await loadMermaid(activeTheme),
                    } satisfies RehypeMermaidOptions,
                ],
            ],
        });

        const { default: Content, ...mdxExports } = await runMDX(mdx, {
            ...runtime,
            baseUrl: import.meta.url,
        });

        const { frontmatter = {} } = mdxExports;
        this.#reactRoot.render(
            <MDXModuleContext.Provider value={mdxModule}>
                <Content
                    frontmatter={frontmatter}
                    components={{
                        wrapper: MDXWrapper,
                        a: MDXAnchor,
                    }}
                />
            </MDXModuleContext.Provider>,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-mdx": AKMDX;
    }
}
