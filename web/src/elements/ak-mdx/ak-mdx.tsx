import { globalAK } from "#common/global";
import "#elements/Alert";
import { AKElement } from "#elements/Base";
import { MDXModuleContext, fetchMDXModule } from "#elements/ak-mdx/MDXModuleContext";
import { MDXAnchor } from "#elements/ak-mdx/components/MDXAnchor";
import { MDXWrapper } from "#elements/ak-mdx/components/MDXWrapper";
import { remarkAdmonition } from "#elements/ak-mdx/remark/remark-admonition";
import { remarkHeadings } from "#elements/ak-mdx/remark/remark-headings";
import { remarkLists } from "#elements/ak-mdx/remark/remark-lists";
import { DistDirectoryName, StaticDirectoryName } from "#paths";
import { compile as compileMDX, run as runMDX } from "@mdx-js/mdx";
import apacheGrammar from "highlight.js/lib/languages/apache";
import diffGrammar from "highlight.js/lib/languages/diff";
import confGrammar from "highlight.js/lib/languages/ini";
import nginxGrammar from "highlight.js/lib/languages/nginx";
import { common } from "lowlight";
import { Root, createRoot } from "react-dom/client";
import * as runtime from "react/jsx-runtime";
import rehypeHighlight from "rehype-highlight";
import { Options as HighlightOptions } from "rehype-highlight";
import rehypeMermaid, { RehypeMermaidOptions } from "rehype-mermaid";
import remarkDirective from "remark-directive";
import remarkFrontmatter from "remark-frontmatter";
import remarkGFM from "remark-gfm";
import remarkMdxFrontmatter from "remark-mdx-frontmatter";
import remarkParse from "remark-parse";
import type { MDXModule } from "~docs/types";

import { css } from "lit";
import { customElement, property } from "lit/decorators.js";

import OneDark from "#common/styles/one-dark.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { UiThemeEnum } from "@goauthentik/api";

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

@customElement("ak-mdx")
export class AKMDX extends AKElement {
    @property({
        reflect: true,
    })
    url: string = "";

    @property()
    content: string = "";

    @property({ attribute: false })
    replacers: Replacer[] = [];

    #reactRoot: Root | null = null;

    resolvedHTML = "";

    static styles = [
        PFBase,
        PFList,
        PFTable,
        PFContent,
        OneDark,
        css`
            :host {
                --ak-mermaid-message-text: var(--pf-c-content--Color);
                --ak-table-stripe-background: var(--pf-global--BackgroundColor--light-200);
            }

            :host([theme="dark"]) {
                --ak-mermaid-message-text: var(--ak-dark-foreground);
                --ak-mermaid-box-background-color: var(--ak-dark-background-lighter);
                --ak-table-stripe-background: var(--pf-global--BackgroundColor--dark-200);
            }

            ak-alert + p {
                margin-block-start: var(--pf-global--spacer--md);
            }

            a {
                --pf-global--link--Color: var(--pf-global--link--Color--light);
                --pf-global--link--Color--hover: var(--pf-global--link--Color--light--hover);
                --pf-global--link--Color--visited: var(--pf-global--link--Color);
            }

            /*
            Note that order of anchor pseudo-selectors must follow:
                1. link
                2. visited
                3. hover
                4. active
            */
            a:link {
                color: var(--pf-global--link--Color);
            }

            a:visited {
                color: var(--pf-global--link--Color--visited);
            }

            a:hover {
                color: var(--pf-global--link--Color--hover);
            }

            a:active {
                color: var(--pf-global--link--Color);
            }

            h2:first-of-type {
                margin-top: 0;
            }

            table thead,
            table tr:nth-child(2n) {
                background-color: var(--ak-table-stripe-background,);
            }

            table td,
            table th {
                border: var(--pf-table-border-width) solid var(--ifm-table-border-color);
                padding: var(--pf-global--spacer--md);
            }

            pre {
                overflow-x: auto;
            }

            pre:has(.hljs) {
                padding: var(--pf-global--spacer--md);
            }

            svg[id^="mermaid-svg-"] {
                .rect {
                    fill: var(
                        --ak-mermaid-box-background-color,
                        var(--pf-global--BackgroundColor--light-300)
                    ) !important;
                }

                .messageText {
                    stroke-width: 4;
                    fill: var(--ak-mermaid-message-text) !important;
                    paint-order: stroke;
                }
            }
        `,
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
        } else {
            nextMDXModule = {
                content: this.content,
            };
        }

        return this.delegateRender(nextMDXModule);
    }

    protected async delegateRender(mdxModule: MDXModule): Promise<void> {
        if (!this.#reactRoot) return;

        const normalized = this.replacers.reduce(
            (content, replacer) => replacer(content),
            mdxModule.content,
        );

        const mdx = await compileMDX(normalized, {
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
                        colorScheme: this.activeTheme === UiThemeEnum.Dark ? "dark" : "light",
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
