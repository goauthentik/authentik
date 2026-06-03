import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-source-kerberos-connectivity")
export class KerberosSourceConnectivity extends AKElement {
    @property()
    connectivity?: {
        [key: string]: {
            [key: string]: string;
        };
    };

    static styles: CSSResult[] = [PFList];

    render(): SlottedTemplateResult {
        if (!this.connectivity) {
            return nothing;
        }
        return html`<ul class="pf-c-list">
            ${Object.keys(this.connectivity).map((serverKey) => {
                return html`<li>${serverKey}: ${this.connectivity![serverKey]}</li>`;
            })}
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-kerberos-connectivity": KerberosSourceConnectivity;
    }
}
