import { docLink } from "@goauthentik/common/global";
import "@goauthentik/elements/Alert";
import { Level } from "@goauthentik/elements/Alert";
import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

export interface MarkdownDocument {
    html: string;
    metadata: { [key: string]: string };
    filename: string;
    path: string;
}

export type Replacer = (input: string, md: MarkdownDocument) => string;

@customElement("ak-markdown")
export class Markdown extends AKElement {
    @property({ attribute: false })
    md?: MarkdownDocument;

    @property({ attribute: false })
    replacers: Replacer[] = [];

    defaultReplacers: Replacer[] = [
        this.replaceAdmonitions,
        this.replaceList,
        this.replaceRelativeLinks,
    ];

    static get styles(): CSSResult[] {
        return [
            PFList,
            PFContent,
            css`
                h2:first-of-type {
                    margin-top: 0;
                }
            `,
        ];
    }

    replaceAdmonitions(input: string): string {
        const admonitionStart = /:::(\w+)<br\s\/>/gm;
        const admonitionEnd = /:::/gm;
        return (
            input
                .replaceAll(admonitionStart, "<ak-alert level='pf-m-$1'>")
                .replaceAll(admonitionEnd, "</ak-alert>")
                // Workaround for admonitions using caution instead of warning
                .replaceAll("pf-m-caution", Level.Warning)
        );
    }

    replaceList(input: string): string {
        return input.replace("<ul>", "<ul class='pf-c-list'>");
    }

    replaceRelativeLinks(input: string, md: MarkdownDocument): string {
        const relativeLink = /href=".(.*)"/gm;
        const cwd = process.env.CWD as string;
        // cwd will point to $root/web, but the docs are in $root/website/docs
        let relPath = md.path.replace(cwd + "site", "");
        if (md.filename === "index.md") {
            relPath = relPath.replace("index.md", "");
        }
        const baseURL = docLink("");
        const fullURL = `${baseURL}${relPath}.$1`;
        return input.replace(relativeLink, `href="${fullURL}" target="_blank"`);
    }

    render(): TemplateResult {
        if (!this.md) {
            return html``;
        }
        let finalHTML = this.md.html;
        const replacers = [...this.defaultReplacers, ...this.replacers];
        replacers.forEach((r) => {
            if (!this.md) {
                return;
            }
            finalHTML = r(finalHTML, this.md);
        });
        return html`${this.md?.metadata.title ? html`<h2>${this.md.metadata.title}</h2>` : html``}
        ${unsafeHTML(finalHTML)}`;
    }
}
