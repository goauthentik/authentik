import { BrandedHTMLPolicy, sanitizeHTML } from "@goauthentik/common/purify";
import { AKElement } from "@goauthentik/elements/Base.js";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FooterLink } from "@goauthentik/api";

const styles = css`
    .pf-c-list a {
        color: unset;
    }
    ul.pf-c-list.pf-m-inline {
        justify-content: center;
        padding: calc(var(--pf-global--spacer--xs) / 2) 0px;
    }
`;

@customElement("ak-brand-links")
export class BrandLinks extends AKElement {
    static get styles() {
        return [PFBase, PFList, styles];
    }

    @property({ type: Array, attribute: false })
    links: FooterLink[] = [];

    render() {
        const links = [...(this.links ?? [])];

        return html` <ul class="pf-c-list pf-m-inline">
            ${map(links, (link) => {
                const children = sanitizeHTML(BrandedHTMLPolicy, link.name);

                if (link.href) {
                    return html`<li><a href="${link.href}">${children}</a></li>`;
                }

                return html`<li>
                    <span> ${children} </span>
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
