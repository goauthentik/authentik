import { purify } from "@goauthentik/common/purify.js";
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

const poweredBy: FooterLink = { name: msg("Powered by authentik"), href: null };

@customElement("ak-brand-links")
export class BrandLinks extends AKElement {
    static get styles() {
        return [PFBase, PFList, styles];
    }

    @property({ type: Array, attribute: false })
    links: FooterLink[] = [];

    render() {
        const links = [...(this.links ?? []), poweredBy];
        return html` <ul class="pf-c-list pf-m-inline">
            ${map(links, (link) =>
                link.href
                    ? purify(html`<li><a href="${link.href}">${link.name}</a></li>`)
                    : html`<li><span>${link.name}</span></li>`,
            )}
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-links": BrandLinks;
    }
}
