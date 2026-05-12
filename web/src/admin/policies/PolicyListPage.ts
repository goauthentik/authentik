import "#admin/policies/PolicyTestForm";
import "#admin/policies/ak-policy-wizard";
import "#admin/policies/dummy/DummyPolicyForm";
import "#admin/policies/event_matcher/EventMatcherPolicyForm";
import "#admin/policies/expiry/ExpiryPolicyForm";
import "#admin/policies/expression/ExpressionPolicyForm";
import "#admin/policies/password/PasswordPolicyForm";
import "#admin/policies/reputation/ReputationPolicyForm";
import "#admin/policies/unique_password/UniquePasswordPolicyForm";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/ConfirmationForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButtonByTagName, modalInvoker } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PolicyWizard } from "#admin/policies/ak-policy-wizard";
import { PolicyTestForm } from "#admin/policies/PolicyTestForm";

import { ModelEnum, PoliciesApi, Policy } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-policy-list")
export class PolicyListPage extends TablePage<Policy> {
    protected override searchEnabled = true;

    public override pageTitle = msg("Policies");
    public override pageDescription = msg(
        "Allow users to use Applications based on properties, enforce Password Criteria and selectively apply Stages.",
    );
    public override pageIcon = "pf-icon pf-icon-infrastructure";

    public override searchPlaceholder = msg("Search for a policy by name or type...");

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Policy>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Actions")],
    ];

    protected override row(item: Policy): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>
                ${(item.boundTo || 0) > 0
                    ? html`<ak-label color=${PFColor.Green} compact>
                          ${msg(str`Assigned to ${item.boundTo} object(s).`)}
                      </ak-label>`
                    : html`<ak-label color=${PFColor.Orange} compact>
                          ${msg("Warning: Policy is not assigned.")}
                      </ak-label>`}`,
            html`${item.verboseName}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButtonByTagName(item.component, item.pk)}
                ${IconPermissionButton(item.name, {
                    model: item.metaModelName as ModelEnum,
                    objectPk: item.pk,
                })}

                <button
                    class="pf-c-button pf-m-plain"
                    ${modalInvoker(
                        PolicyTestForm,
                        { policy: item },
                        {
                            closedBy: "closerequest",
                        },
                    )}
                >
                    <pf-tooltip position="top" content=${msg("Test")}>
                        <i class="fas fa-vial" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </div>`,
        ];
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Policy / Policies")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Policy) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesAllUsedByList({
                    policyUuid: item.pk,
                });
            }}
            .delete=${(item: Policy) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesAllDestroy({
                    policyUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`
            <button
                class="pf-c-button pf-m-primary"
                type="button"
                aria-description="${msg("Open the wizard to create a new policy.")}"
                ${PolicyWizard.asModalInvoker()}
            >
                ${msg("New Policy")}
            </button>
        `;
    }

    protected override renderToolbar(): SlottedTemplateResult {
        return html`${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${msg("Successfully cleared policy cache")}
                errorMessage=${msg("Failed to delete policy cache")}
                action=${msg("Clear Cache")}
                .onConfirm=${() => {
                    return new PoliciesApi(DEFAULT_CONFIG).policiesAllCacheClearCreate();
                }}
            >
                <span slot="header">${msg("Clear Policy cache")}</span>
                <p slot="body">
                    ${msg(
                        "Are you sure you want to clear the policy cache? This will cause all policies to be re-evaluated on their next usage.",
                    )}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                    ${msg("Clear cache")}
                </button>
                <div slot="modal"></div>
            </ak-forms-confirm>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-list": PolicyListPage;
    }
}
