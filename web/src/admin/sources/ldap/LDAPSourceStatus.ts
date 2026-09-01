import "#elements/timestamp/ak-timestamp";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/tasks/TaskStatus";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import { LDAPSourceSync, LDAPSourceSyncStatusEnum } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

function statusBlock(notice: string, status: LDAPSourceSyncStatusEnum, timestamp: Date | null) {
    const akTaskStatus = html`<ak-task-status .status=${status}></ak-task-status>`;
    return timestamp === null
        ? html`${akTaskStatus} ${msg("Task has not yet completed")}`
        : html` <div class="ak-source-ldap-status-timestamp">
              ${akTaskStatus}
              <span>${notice} <ak-timestamp .timestamp=${timestamp}></ak-timestamp></span>
          </div>`;
}

const Styles = css`
    .ak-source-ldap-status-timestamp {
        display: flex;
        align-items: center;
        gap: var(--pf-global--spacer--sm, 0.5rem);
    }
    .ak-source-ldap-status-timestamp > span {
        display: flex;
        align-items: center;
        align-content: flex-start;
        gap: var(--pf-global--spacer--xs, 0.25rem);
    }
`;

@customElement("ak-source-ldap-status")
export class LDAPSourceStatus extends AKElement {
    @property()
    connectivity: {
        [key: string]: {
            [key: string]: string;
        };
    } | null = null;

    @property({ attribute: false })
    lastSync?: LDAPSourceSync;

    static styles: CSSResult[] = [PFDescriptionList, PFList, Styles];

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
                    match(this.lastSync?.status ?? null)
                        .with(null, () => html`${msg("No synchronization status available.")}`)
                        .with(LDAPSourceSyncStatusEnum.Running, (status) =>
                            statusBlock(
                                msg("Started: "),
                                status,
                                /* @ts-expect-error ts2551 OpenAPI workaround */
                                this.lastSync?.startedAt ?? this.lastSync?.started_at ?? null,
                            ),
                        )
                        .otherwise((status) =>
                            statusBlock(
                                msg("Finished: "),
                                status,
                                /* @ts-expect-error ts2551 OpenAPI workaround */
                                this.lastSync?.finishedAt ?? this.lastSync?.finished_at ?? null,
                            ),
                        ),
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
