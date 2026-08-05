import "#elements/buttons/ModalButton";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#user/agents/UserAgentForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { formatElapsedTime } from "#common/temporal";

import { IconTokenCopyButton } from "#elements/buttons/IconTokenCopyButton";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Agent, AgentsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-agent-list")
export class UserAgentList extends Table<Agent> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "username";

    public override label = msg("Agents", { id: "agent.verbose-name-plural.label" });
    protected override emptyStateMessage = msg("No agents.", { id: "agent.list.empty" });

    async apiEndpoint(): Promise<PaginatedResponse<Agent>> {
        // The API scopes this to agents the current user owns (via `owner_field`).
        return aki(AgentsApi).agentsAgentsList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Name", { id: "agent.column.name" }), "username"],
        [msg("Expires", { id: "agent.column.expires" }), "expires"],
        [msg("Actions", { id: "agent.column.actions" }), null, msg("Row Actions")],
    ];

    protected override rowLabel(item: Agent): string | null {
        return item.name || item.username;
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal
                keep-open-after-submit
                cancelText=${msg("Close", { id: "agent.form.close.label" })}
                @ak-modal-hide=${() => this.fetch()}
            >
                <span slot="submit">${msg("Create", { id: "agent.create.submit" })}</span>
                <span slot="header">${msg("Create Agent", { id: "agent.create.header" })}</span>
                <ak-user-agent-form slot="form"></ak-user-agent-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Create Agent", { id: "agent.create.trigger" })}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }

    renderToolbarSelected(): TemplateResult {
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

    row(item: Agent): SlottedTemplateResult[] {
        return [
            html`<div>${item.name || item.username}</div>
                <small class="pf-m-monospace">${item.username}</small>`,
            item.expiring && item.expires
                ? html`<pf-tooltip position="top" .content=${item.expires.toLocaleString()}>
                      ${formatElapsedTime(item.expires)}
                  </pf-tooltip>`
                : html`${msg("-", { id: "agent.expires.never" })}`,
            html`${IconTokenCopyButton(item.tokenIdentifier)}
                <ak-forms-delete-bulk
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
        "ak-user-agent-list": UserAgentList;
    }
}
