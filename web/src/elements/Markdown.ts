import "@goauthentik/elements/Alert";
import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, PropertyValues, css, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

export type Replacer = (input: string) => string;

@customElement("ak-markdown")
export class Markdown extends AKElement {
    @property()
    content: string = "";

    @property()
    meta: string = "";

    @property({ attribute: false })
    replacers: Replacer[] = [];

    resolvedHTML = "";

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

    protected firstUpdated(changedProperties: PropertyValues): void {
        super.updated(changedProperties);

        const headingLinks =
            this.shadowRoot?.querySelectorAll<HTMLAnchorElement>("a.markdown-heading") ?? [];

        for (const headingLink of headingLinks) {
            headingLink.addEventListener("click", (ev) => {
                ev.preventDefault();

                const url = new URL(headingLink.href);
                const elementID = url.hash.slice(1);

                const target = this.shadowRoot?.getElementById(elementID);

                if (!target) {
                    console.warn(`Element with ID ${elementID} not found`);
                    return;
                }

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            });
        }
    }

    willUpdate(properties: PropertyValues<this>) {
        if (properties.has("content")) {
            this.resolvedHTML = this.replacers.reduce(
                (html, replacer) => replacer(html),
                this.content,
            );
        }
    }

    render() {
        if (!this.content) return nothing;

        return unsafeHTML(this.resolvedHTML);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-markdown": Markdown;
    }
}
