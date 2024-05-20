import { AKElement } from "@goauthentik/elements/Base";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-source-ldap-connectivity")
export class LDAPSourceConnectivity extends AKElement {
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
                let serverLabel = html`${serverKey}`;
                if (serverKey === "__all__") {
                    serverLabel = html`<b>${msg("Global status")}</b>`;
                }
                const server = this.connectivity![serverKey];
                const content = html`${serverLabel}: ${server.status}`;
                let tooltip = html`${content}`;
                if (server.status === "ok") {
                    tooltip = html`<pf-tooltip position="top">
                        <ul slot="content" class="pf-c-list">
                            <li>${msg("Vendor")}: ${server.vendor}</li>
                            <li>${msg("Version")}: ${server.version}</li>
                        </ul>
                        ${content}
                    </pf-tooltip>`;
                }
                return html`<li>${tooltip}</li>`;
            })}
        </ul>`;
    }
}
