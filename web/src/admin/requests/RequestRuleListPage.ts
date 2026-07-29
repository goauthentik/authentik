import "#admin/rbac/ObjectPermissionModal";
import "#admin/requests/RequestRuleForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/policies/BoundPoliciesList";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { RequestRuleForm } from "#admin/requests/RequestRuleForm";

import { ModelEnum, RequestRule, RequestsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-request-rule-list")
export class RequestRuleListPage extends TablePage<RequestRule> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a request rule by name...");
    public override pageTitle = msg("Request Rules");
    public override pageDescription = msg(
        "Define who can approve access requests for the objects these rules are bound to.",
    );
    public override pageIcon = "pf-icon pf-icon-locked";
    public override expandable = true;

    public override order = "name";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<RequestRule>> {
        return aki(RequestsApi).requestsRulesList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Bound to")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html` <ak-forms-delete-bulk
            object-label=${msg("Request rule(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: RequestRule) => {
                return aki(RequestsApi).requestsRulesUsedByList({
                    uuid: item.uuid || "",
                });
            }}
            .delete=${(item: RequestRule) => {
                return aki(RequestsApi).requestsRulesDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: RequestRule): SlottedTemplateResult[] {
        return [
            item.name,
            msg(str`${item.targets.length} object(s)`),
            html`<div class="ak-c-table__actions">
                ${IconEditButton(RequestRuleForm, item.uuid, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikRequestsRequestrule}
                    objectPk=${item.uuid!}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderExpanded(item: RequestRule): SlottedTemplateResult {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list
                .target=${item.pbmUuid}
                .policyEngineMode=${item.policyEngineMode}
            >
                <span slot="description"
                    >${msg("These bindings control which users/groups can approve requests.")}</span
                >
            </ak-bound-policies-list>
        </div>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(RequestRuleForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-rule-list": RequestRuleListPage;
    }
}
