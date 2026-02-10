import { globalAK } from "#common/global";
import { BrandedHTMLPolicy, sanitizeHTML } from "#common/purify";

import { AKElement } from "#elements/Base";

import { FooterLink } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

/**
 * @part list - The list element containing the links
 * @part list-item - Each item in the list, including the "Powered by authentik" item
 * @part list-item-link - The link element for each item, if applicable
 */
@customElement("ak-brand-links")
export class BrandLinks extends AKElement {
    static styles = [PFList];

    @property({ type: Array, attribute: false })
    public links: FooterLink[] = globalAK().brand.uiFooterLinks || [];

    render() {
        return html`<ul aria-label=${msg("Site links")} class="pf-c-list pf-m-inline" part="list">
            ${map(this.links, (link) => {
                const children = sanitizeHTML(BrandedHTMLPolicy, link.name);

                if (link.href) {
                    return html`<li part="list-item">
                        <a part="list-item-link" href=${link.href}>${children}</a>
                    </li>`;
                }

                return html`<li part="list-item">
                    <span>${children}</span>
                </li>`;
            })}
            <li part="list-item"><span>${msg("Powered by authentik")}</span></li>
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-links": BrandLinks;
    }
}
