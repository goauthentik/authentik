import "#elements/buttons/ModalButton";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#user/user-settings/agents/UserAgentForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { globalAK } from "#common/global";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Agent, AgentsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-agent-list")
export class UserAgentList extends Table<Agent> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "username";

    public override label = msg("Agents");
    protected override emptyStateMessage = msg("No agents.");

    async apiEndpoint(): Promise<PaginatedResponse<Agent>> {
        // The API scopes this to agents the current user owns (via `owner_field`).
        return aki(AgentsApi).agentsAgentsList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Expires"), "expires"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override rowLabel(item: Agent): string | null {
        return item.name || item.username;
    }

    #selfServiceEnabled(): boolean {
        return Boolean(globalAK().brand.flags.enterpriseAgentAllowAny);
    }

    renderToolbar(): TemplateResult {
        return html`
            ${this.#selfServiceEnabled()
                ? html`<ak-forms-modal>
                      <span slot="submit">${msg("Create")}</span>
                      <span slot="header">${msg("Create Agent")}</span>
                      <ak-user-agent-form slot="form"></ak-user-agent-form>
                      <button slot="trigger" class="pf-c-button pf-m-secondary">
                          ${msg("Create Agent")}
                      </button>
                  </ak-forms-modal>`
                : nothing}
            ${super.renderToolbar()}
        `;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Agent(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Agent) => [{ key: msg("Name"), value: item.name || item.username }]}
            .delete=${(item: Agent) =>
                aki(AgentsApi).agentsAgentsDestroy({
                    id: item.pk,
                })}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
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
                : html`${msg("-")}`,
            html`<ak-forms-delete-bulk
                object-label=${msg("Agent")}
                .objects=${[item]}
                .delete=${(agent: Agent) =>
                    aki(AgentsApi).agentsAgentsDestroy({
                        id: agent.pk,
                    })}
            >
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Delete")}>
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
