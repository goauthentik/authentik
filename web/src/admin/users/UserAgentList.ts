import "#elements/forms/DeleteBulkForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Agent, AgentsApi, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-admin-user-agent-list")
export class AdminUserAgentList extends Table<Agent> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override order = "username";

    @property({ attribute: false })
    public user?: User;

    protected override async apiEndpoint(): Promise<PaginatedResponse<Agent>> {
        if (!this.user) {
            throw new TypeError("User is not set, cannot fetch agents.");
        }

        return aki(AgentsApi).agentsAgentsList({
            ...(await this.defaultEndpointConfig()),
            parent: this.user.pk,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name", { id: "agent.column.name" }), "username"],
        [msg("Expires", { id: "agent.column.expires" }), "expires"],
        [msg("Actions", { id: "agent.column.actions" }), null, msg("Row Actions")],
    ];

    protected override rowLabel(item: Agent): string | null {
        return item.name || item.username;
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Agent(s)", { id: "agent.delete.object-label" })}
            .objects=${this.selectedElements}
            .metadata=${(item: Agent) => [
                {
                    key: msg("Name", { id: "agent.column.name" }),
                    value: item.name || item.username,
                },
            ]}
            .delete=${(item: Agent) =>
                aki(AgentsApi).agentsAgentsDestroy({
                    id: item.pk,
                })}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete", { id: "agent.delete.trigger" })}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: Agent): SlottedTemplateResult[] {
        return [
            html`<div>${item.name || item.username}</div>
                <small class="pf-m-monospace">${item.username}</small>`,
            item.expiring && item.expires
                ? html`<pf-tooltip position="top" .content=${item.expires.toLocaleString()}>
                      ${formatElapsedTime(item.expires)}
                  </pf-tooltip>`
                : html`${msg("-", { id: "agent.expires.never" })}`,
            html`<ak-forms-delete-bulk
                object-label=${msg("Agent", { id: "agent.delete.object-label-single" })}
                .objects=${[item]}
                .delete=${(agent: Agent) =>
                    aki(AgentsApi).agentsAgentsDestroy({
                        id: agent.pk,
                    })}
            >
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip
                        position="top"
                        content=${msg("Delete", { id: "agent.delete.tooltip" })}
                    >
                        <i aria-hidden="true" class="fas fa-trash"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-delete-bulk>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-user-agent-list": AdminUserAgentList;
    }
}
