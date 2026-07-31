import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { aki } from "#common/api/client";

import { ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AgentForm } from "#admin/agents/AgentForm";

import { Agent, AgentsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-agent-list")
export class AgentListPage extends TablePage<Agent> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a agent...");
    public override pageTitle = msg("Agents");
    public override pageDescription = msg(
        "Admin-provisioned delegate identities that access can be requested and granted for, separately from their parent user.",
    );
    public override pageIcon = "pf-icon pf-icon-user";

    public override order = "username";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<Agent>> {
        return aki(AgentsApi).agentsAgentsList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Parent")],
        [msg("Expires"), "expires"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html` <ak-forms-delete-bulk
            object-label=${msg("Agent(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: Agent) => {
                return aki(AgentsApi).agentsAgentsDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: Agent): SlottedTemplateResult[] {
        return [
            html`<div>${item.username}</div>
                <small>${item.name}</small>`,
            item.parent
                ? html`<a href="#/identity/users/${item.parent.pk}">
                      <div>${item.parent.username}</div>
                      <small>${item.parent.name}</small>
                  </a>`
                : html`<span class="pf-u-color-200">${msg("-")}</span>`,
            item.expiring && item.expires ? Timestamp(item.expires) : msg("Never"),
            html`<ak-forms-delete-bulk
                object-label=${msg("Agent")}
                .objects=${[item]}
                .delete=${(agent: Agent) => {
                    return aki(AgentsApi).agentsAgentsDestroy({
                        id: agent.pk,
                    });
                }}
            >
                <button slot="trigger" class="pf-c-button pf-m-danger pf-m-small">
                    ${msg("Delete")}
                </button>
            </ak-forms-delete-bulk>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(AgentForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-agent-list": AgentListPage;
    }
}
