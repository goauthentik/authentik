import { AKElement } from "@goauthentik/elements/Base";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-source-kerberos-connectivity")
export class KerberosSourceConnectivity extends AKElement {
    @property()
    connectivity?: {
        [key: string]: {
            [key: string]: string;
        };
    };

    static get styles(): CSSResult[] {
        return [PFBase, PFList];
    }

    render(): TemplateResult {
        if (!this.connectivity) {
            return html``;
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
