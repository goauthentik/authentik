import "#elements/timestamp/ak-timestamp";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/tasks/TaskStatus";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import { KerberosSourceSync, SyncStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-source-kerberos-status")
export class KerberosSourceStatus extends AKElement {
    public static styles: CSSResult[] = [PFDescriptionList, PFList];

    @property({ attribute: false })
    public connectivity: Record<string, Record<string, string>> | null = null;

    @property({ attribute: false })
    public lastSync: KerberosSourceSync | null = null;

    protected renderConnectivity(): SlottedTemplateResult {
        if (!this.connectivity) {
            return msg("No connectivity status available.");
        }

        return html`
            <ul class="pf-c-list">
                ${Array.from(Object.entries(this.connectivity), ([key, server]) => {
                    const serverLabel: SlottedTemplateResult = key;

                    return html`<li>${serverLabel}: ${server.status}</li>`;
                })}
            </ul>
        `;
    }

    protected renderLastSync(): SlottedTemplateResult {
        const { lastSync } = this;

        if (!lastSync) {
            return msg("Synchronisation never ran.");
        }

        const status =
            lastSync.status !== null
                ? html`<ak-task-status .status=${lastSync.status}></ak-task-status>`
                : msg("No synchronization status available");
        const time =
            lastSync.status === SyncStatusEnum.Running
                ? html`${msg("Started")}
                      <ak-timestamp .timestamp=${lastSync.startedAt ?? null}></ak-timestamp>`
                : html`${msg("Finished")}
                      <span
                          ><ak-timestamp .timestamp=${lastSync.startedAt ?? null}></ak-timestamp
                      ></span>`;

        return html`
            <ul class="pf-c-list">
                <li>${status}</li>
                <li>${time}</li>
                <li>Users: ${lastSync.usersCount ?? 0}</li>
            </ul>
        `;
    }

    render(): SlottedTemplateResult {
        return renderDescriptionList(
            [
                [msg("Connection"), this.renderConnectivity()],
                [msg("Last synchronisation"), this.renderLastSync()],
            ],
            { twocolumn: true },
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-kerberos-status": KerberosSourceStatus;
    }
}
