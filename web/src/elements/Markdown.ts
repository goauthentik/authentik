import { docLink } from "@goauthentik/common/global";
import "@goauthentik/elements/Alert";
import { Level } from "@goauthentik/elements/Alert";
import { AKElement } from "@goauthentik/elements/Base";
import { matter } from "md-front-matter";
import * as showdown from "showdown";

import { CSSResult, PropertyValues, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

export interface MarkdownDocument {
    path: string;
}

export type Replacer = (input: string, md: MarkdownDocument) => string;

const isRelativeLink = /href="(\.[^"]*)"/gm;
const isFile = /[^/]+\.md/;

@customElement("ak-markdown")
export class Markdown extends AKElement {
    @property()
    md: string = "";

    @property()
    meta: string = "";

    @property({ attribute: false })
    replacers: Replacer[] = [];

    docHtml = "";
    docTitle = "";

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

    converter = new showdown.Converter({ metadata: true, tables: true });

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
        const baseName = md.path.replace(isFile, "");
        const baseUrl = docLink("");
        return input.replace(isRelativeLink, (_match, path) => {
            const pathName = path.replace(".md", "");
            const link = `docs/${baseName}${pathName}`;
            const url = new URL(link, baseUrl).toString();
            return `href="${url}" _target="blank"`;
        });
    }

    willUpdate(properties: PropertyValues<this>) {
        if (properties.has("md") || properties.has("meta")) {
            const parsedContent = matter(this.md);
            const parsedHTML = this.converter.makeHtml(parsedContent.content);
            const replacers = [...this.defaultReplacers, ...this.replacers];
            this.docTitle = parsedContent.data["title"] ?? "";
            this.docHtml = replacers.reduce(
                (html, replacer) => replacer(html, { path: this.meta }),
                parsedHTML,
            );
        }
    }

    render() {
        if (!this.md) {
            return nothing;
        }

        return html`${this.docTitle ? html`<h2>${this.docTitle}</h2>` : nothing}
        ${unsafeHTML(this.docHtml)}`;
    }
}
