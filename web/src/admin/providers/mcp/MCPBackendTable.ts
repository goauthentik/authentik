import "#elements/forms/DeleteBulkForm";
import { aki } from "#common/api/client";

import { IconEditButton, modalInvoker } from "#elements/dialogs";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { renderBoundPoliciesExpansion } from "#admin/policies/renderPolicyBindings";
import { MCPBackendForm } from "#admin/providers/mcp/MCPBackendForm";

import { MCPBackend, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-mcp-backend-list")
export class MCPBackendTable extends Table<MCPBackend> {
    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "name";

    @property({ type: Number })
    public gateway?: number;

    protected override async apiEndpoint(): Promise<PaginatedResponse<MCPBackend>> {
        return aki(ProvidersApi).providersMcpBackendsList({
            ...(await this.defaultEndpointConfig()),
            gateway: this.gateway,
        });
    }

    protected override rowLabel(item: MCPBackend): string {
        return item.name;
    }

    protected columns: TableColumn[] = [
        [msg("Name", { id: "mcp-backend.table.name.label" }), "name"],
        [msg("Slug", { id: "mcp-backend.table.slug.label" }), "slug"],
        [msg("URL", { id: "mcp-backend.table.url.label" })],
        [msg("Actions", { id: "mcp-backend.table.actions.label" }), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        return html`<ak-forms-delete-bulk
            object-label=${msg("MCP Backend(s)", { id: "mcp-backend.table.delete.label" })}
            .objects=${this.selectedElements}
            .delete=${(item: MCPBackend) =>
                aki(ProvidersApi).providersMcpBackendsDestroy({ pbmUuid: item.pbmUuid })}
        >
            <button
                ?disabled=${this.selectedElements.length < 1}
                slot="trigger"
                class="pf-c-button pf-m-danger"
            >
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderToolbar(): SlottedTemplateResult {
        return [
            html`<button
                class="pf-c-button pf-m-primary"
                ${modalInvoker(MCPBackendForm, { gateway: this.gateway })}
            >
                ${msg("Create", { id: "mcp-backend.table.create.label" })}
            </button>`,
            super.renderToolbar(),
        ];
    }

    protected override row(item: MCPBackend): SlottedTemplateResult[] {
        return [
            item.name,
            html`<code>${item.slug}</code>`,
            html`<code>${item.url}</code>`,
            IconEditButton(MCPBackendForm, item.pbmUuid, item.name),
        ];
    }

    protected override renderExpanded(item: MCPBackend): SlottedTemplateResult {
        return renderBoundPoliciesExpansion({
            target: item.pbmUuid,
            mode: item.policyEngineMode,
            description: html`${msg(
                "These bindings are evaluated for every tool of this backend. Expression policies can access the tool via context['mcp']['tool'], and the call's arguments via context['mcp']['arguments'] (None when listing tools).",
                { id: "mcp-backend.table.policies.description" },
            )}`,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-mcp-backend-list": MCPBackendTable;
    }
}
