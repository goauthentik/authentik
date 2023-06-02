import "@goauthentik/admin/policies/PolicyTestForm";
import "@goauthentik/admin/policies/PolicyWizard";
import "@goauthentik/admin/policies/dummy/DummyPolicyForm";
import "@goauthentik/admin/policies/event_matcher/EventMatcherPolicyForm";
import "@goauthentik/admin/policies/expiry/ExpiryPolicyForm";
import "@goauthentik/admin/policies/expression/ExpressionPolicyForm";
import "@goauthentik/admin/policies/password/PasswordPolicyForm";
import "@goauthentik/admin/policies/reputation/ReputationPolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/forms/ConfirmationForm";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PoliciesApi, Policy } from "@goauthentik/api";

@customElement("ak-policy-list")
export class PolicyListPage extends TablePage<Policy> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Policies");
    }
    pageDescription(): string {
        return msg(
            "Allow users to use Applications based on properties, enforce Password Criteria and selectively apply Stages.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-infrastructure";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Policy>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Type")),
            new TableColumn(msg("Actions")),
        ];
    }

    row(item: Policy): TemplateResult[] {
        return [
            html`<div>${item.name}</div>
                ${(item.boundTo || 0) > 0
                    ? html`<ak-label color=${PFColor.Green} ?compact=${true}>
                          ${msg(str`Assigned to ${item.boundTo} object(s).`)}
                      </ak-label>`
                    : html`<ak-label color=${PFColor.Orange} ?compact=${true}>
                          ${msg("Warning: Policy is not assigned.")}
                      </ak-label>`}`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg(str`Update ${item.verboseName}`)} </span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.pk,
                        }}
                        type=${ifDefined(item.component)}
                    >
                    </ak-proxy-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-pencil-alt" aria-hidden="true"></i>
                    </button>
                </ak-forms-modal>
                <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                    <span slot="submit"> ${msg("Test")} </span>
                    <span slot="header"> ${msg("Test Policy")} </span>
                    <ak-policy-test-form slot="form" .policy=${item}> </ak-policy-test-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-vial" aria-hidden="true"></i>
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Policy / Policies")}
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

    renderObjectCreate(): TemplateResult {
        return html`<ak-policy-wizard> </ak-policy-wizard>`;
    }

    renderToolbar(): TemplateResult {
        return html` ${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${msg("Successfully cleared policy cache")}
                errorMessage=${msg("Failed to delete policy cache")}
                action=${msg("Clear cache")}
                .onConfirm=${() => {
                    return new PoliciesApi(DEFAULT_CONFIG).policiesAllCacheClearCreate();
                }}
            >
                <span slot="header"> ${msg("Clear Policy cache")} </span>
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
