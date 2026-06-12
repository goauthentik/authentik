import "#elements/Alert";
import "#elements/Diagram/ak-diagram";
import "#elements/ak-mdx/components/ak-md-a";

import { globalAK } from "#common/global";
import { BrandedHTMLPolicy, CompiledMarkdownSanitizePolicy, sanitizeHTML } from "#common/purify";

import { compileRuntimeMarkdown } from "#elements/ak-mdx/markdown";
import Styles from "#elements/ak-mdx/styles.css";
import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { DistDirectoryName, StaticDirectoryName } from "#paths";
import OneDark from "#styles/atom/one-dark.css";

import { customElement, property, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";

/**
 * The JSON envelope our build-time `mdx-plugin` emits for every imported
 * `.md` / `.mdx` file: the `content` field is **pre-rendered HTML**, not
 * raw markdown source.
 */
interface MarkdownModule {
    content: string;
    frontmatter?: Record<string, unknown>;
    publicPath?: string;
    publicDirectory?: string;
}

async function fetchMarkdownModule(url: string | URL): Promise<MarkdownModule> {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Failed to fetch markdown: ${response.statusText}`);
    return response.json();
}

/**
 * A replacer applied to the compiled HTML before it is stamped into the
 * shadow DOM. Used by callers who need to substitute `{placeholder}`-style
 * tokens (e.g. proxy-provider sample configs).
 */
export type Replacer = (input: string) => string;

/**
 * Renders markdown into shadow DOM with no client-side JavaScript
 * evaluation. Two modes:
 *
 * - `url`: resolves to a JSON envelope produced by the build-time
 *   `mdx-plugin`. The envelope's `content` is already HTML.
 * - `content`: an admin-supplied markdown string. Compiled in-browser
 *   through a pure `unified` / remark / rehype pipeline (no `eval`,
 *   no `Function`), then sanitized via `BrandedHTMLPolicy`.
 */
@customElement("ak-mdx")
export class AKMDX extends AKElement {
    @property({ type: String, reflect: true, useDefault: true })
    public url: string | null = null;

    @property()
    public content?: string;

    @property({ attribute: false })
    public replacers: Replacer[] = [];

    @state()
    protected compiledTemplate: SlottedTemplateResult = null;

    static styles = [
        // ---
        PFList,
        PFTable,
        PFContent,
        OneDark,
        Styles,
    ];

    public override async connectedCallback() {
        super.connectedCallback();
        await this.hydrate();
    }

    #applyReplacers(html: string): string {
        return this.replacers.reduce((acc, replacer) => replacer(acc), html);
    }

    /**
     * URL mode: HTML comes from our build-time pipeline. `replacers` may
     * splice dynamic, sometimes admin-controlled, values into it (see
     * `ProxyProviderViewPage`), so the post-replacer string is routed
     * through {@linkcode CompiledMarkdownSanitizePolicy} — a DOMPurify
     * policy that preserves the custom elements our pipeline emits
     * (`<ak-alert>`, `<ak-md-a>`, `<ak-diagram>`) while stripping anything
     * a replacer could have injected.
     */
    async #hydrateFromURL(url: string): Promise<SlottedTemplateResult> {
        const { relBase } = globalAK().api;
        const pathname =
            relBase +
            StaticDirectoryName +
            "/" +
            DistDirectoryName +
            url.slice(url.indexOf("/assets"));
        const module = await fetchMarkdownModule(pathname);

        if (module.publicDirectory) {
            this.dataset.publicDirectory = module.publicDirectory;
        }

        const trustedHTML = CompiledMarkdownSanitizePolicy.createHTML(
            this.#applyReplacers(module.content),
        );

        return unsafeHTML(trustedHTML.toString());
    }

    /**
     * Content mode: admin-supplied markdown compiled in-browser through
     * a pure `unified` / remark / rehype pipeline (no `eval`, no
     * `Function`), then sanitized via `BrandedHTMLPolicy`.
     */
    async #hydrateFromContent(source: string): Promise<SlottedTemplateResult> {
        const html = this.#applyReplacers(await compileRuntimeMarkdown(source));
        return sanitizeHTML(BrandedHTMLPolicy, html);
    }

    /**
     * Resolve `url` or `content` into a template result and stash it on
     * reactive state. After this completes, Lit's render takes over.
     */
    protected async hydrate(): Promise<void> {
        this.compiledTemplate = this.url
            ? await this.#hydrateFromURL(this.url)
            : await this.#hydrateFromContent(this.content ?? "");
    }

    public override render(): SlottedTemplateResult {
        return this.compiledTemplate;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-mdx": AKMDX;
    }
}
