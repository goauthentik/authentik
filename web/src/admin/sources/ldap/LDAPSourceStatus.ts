import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/tasks/TaskStatus";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import { LDAPSourceSync } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-source-ldap-status")
export class LDAPSourceStatus extends AKElement {
    @property()
    connectivity: {
        [key: string]: {
            [key: string]: string;
        };
    } | null = null;

    @property()
    lastSync?: LDAPSourceSync;

    static styles: CSSResult[] = [PFDescriptionList, PFList];

    render(): SlottedTemplateResult {
        return html`
            ${renderDescriptionList([
                [
                    msg("Connection"),
                    this.connectivity
                        ? html`
                              <ul class="pf-c-list">
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
                              </ul>
                          `
                        : html`${msg("No connectivity status available.")}`,
                ],
                [
                    msg("Last synchronisation"),
                    this.lastSync !== undefined
                        ? html`
                              <ak-task-status .status=${this.lastSync.status}></ak-task-status>
                              ${this.lastSync.finishedAt}
                          `
                        : html`${msg("Synchronisation never ran.")}`,
                ],
            ])}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-status": LDAPSourceStatus;
    }
}
