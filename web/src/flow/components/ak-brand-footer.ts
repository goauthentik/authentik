import { BrandedHTMLPolicy, sanitizeHTML } from "#common/purify";

import { AKElement } from "#elements/Base";

import { FooterLink } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const styles = css`
    .pf-c-list a {
        color: unset;
    }
    ul.pf-c-list.pf-m-inline {
        justify-content: center;
        padding: 0;
        padding-block-start: calc(var(--pf-global--spacer--xs) / 2);
        column-gap: var(--pf-global--spacer--xl);
        row-gap: var(--pf-global--spacer--md);
    }
`;

@customElement("ak-brand-links")
export class BrandLinks extends AKElement {
    static styles = [PFBase, PFList, styles];

    @property({ type: Array, attribute: false })
    links: FooterLink[] = [];

    render() {
        const links = [...(this.links ?? [])];

        return html` <ul aria-label=${msg("Site links")} class="pf-c-list pf-m-inline">
            ${map(links, (link) => {
                const children = sanitizeHTML(BrandedHTMLPolicy, link.name);

                if (link.href) {
                    return html`<li><a href="${link.href}">${children}</a></li>`;
                }

                return html`<li>
                    <span> ${children}</span>
                </li>`;
            })}
            <li><span>${msg("Powered by authentik")}</span></li>
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-links": BrandLinks;
    }
}
