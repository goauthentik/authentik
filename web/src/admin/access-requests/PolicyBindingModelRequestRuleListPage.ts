import "#admin/access-requests/PolicyBindingModelRequestRuleForm";
import "#elements/forms/DeleteBulkForm";
import "#admin/policies/BoundPoliciesList";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PolicyBindingModelRequestRuleForm } from "#admin/access-requests/PolicyBindingModelRequestRuleForm";
import { renderTargetSummary } from "#admin/access-requests/RequestableTargetHelpers";

import { PamApi, PolicyBindingModelRequestRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

@customElement("ak-pbm-request-rule-list")
export class PolicyBindingModelRequestRuleListPage extends TablePage<PolicyBindingModelRequestRule> {
    public override checkbox = true;
    public override searchEnabled = true;
    public override expandable = true;

    public pageTitle = msg("Request Rules");
    public pageDescription = msg(
        "Control who can request access to an Application or Application Entitlement, and who must approve it. A single rule can cover several targets at once.",
    );
    public pageIcon = "pf-icon pf-icon-security";

    protected async apiEndpoint(): Promise<PaginatedResponse<PolicyBindingModelRequestRule>> {
        return aki(PamApi).pamRequestRulesList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [[msg("Name"), "name"], [msg("Targets")], [msg("Actions")]];

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PolicyBindingModelRequestRuleForm);
    }

    protected override renderExpanded(item: PolicyBindingModelRequestRule): SlottedTemplateResult {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list
                .target=${item.pbmUuid}
                .policyEngineMode=${item.policyEngineMode}
            >
                <span slot="description"
                    >${msg(
                        "These bindings control if this stage will be applied to the flow.",
                    )}</span
                >
            </ak-bound-policies-list>
        </div>`;
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Request Rule(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: PolicyBindingModelRequestRule) => {
                return aki(PamApi).pamRequestRulesUsedByList({
                    uuid: item.uuid || "",
                });
            }}
            .delete=${(item: PolicyBindingModelRequestRule) => {
                return aki(PamApi).pamRequestRulesDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected row(item: PolicyBindingModelRequestRule): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            renderTargetSummary(item.pbmTargets),
            html`<div class="ak-c-table__actions">
                ${IconEditButton(PolicyBindingModelRequestRuleForm, item.uuid)}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pbm-request-rule-list": PolicyBindingModelRequestRuleListPage;
    }
}
