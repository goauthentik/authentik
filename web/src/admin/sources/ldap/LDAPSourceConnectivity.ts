import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-source-ldap-connectivity")
export class LDAPSourceConnectivity extends AKElement {
    @property()
    connectivity: {
        [key: string]: {
            [key: string]: string;
        };
    } | null = null;

    static styles: CSSResult[] = [PFList];

    render(): SlottedTemplateResult {
        if (!this.connectivity) {
            return html`${msg("No connectivity status available.")}`;
        }

        const servers = Object.entries(this.connectivity);

        return html`<ul class="pf-c-list">
            ${map(servers, ([key, server]) => {
                const label = key === "__all__" ? html`<b>${msg("Global status")}</b>` : key;
                const content = html`${label}: ${server.status}`;
                return html`<li>
                    ${server.status === "ok"
                        ? html`<pf-tooltip position="top">
                              <ul slot="content" class="pf-c-list">
                        <li>${msg("Vendor")}: ${server.vendor}</Li>
                        <li>${msg("Version")}: ${server.version}</li>
                              </ul>
                              ${content}
                          </pf-tooltip>`
                        : content}
                </li>`;
            })}
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-connectivity": LDAPSourceConnectivity;
    }
}
