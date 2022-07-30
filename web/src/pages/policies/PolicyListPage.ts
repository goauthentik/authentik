import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { uiConfig } from "@goauthentik/web/common/config";
import "@goauthentik/web/elements/forms/ConfirmationForm";
import "@goauthentik/web/elements/forms/DeleteBulkForm";
import "@goauthentik/web/elements/forms/ModalForm";
import "@goauthentik/web/elements/forms/ProxyForm";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TablePage } from "@goauthentik/web/elements/table/TablePage";
import "@goauthentik/web/pages/policies/PolicyTestForm";
import "@goauthentik/web/pages/policies/PolicyWizard";
import "@goauthentik/web/pages/policies/dummy/DummyPolicyForm";
import "@goauthentik/web/pages/policies/event_matcher/EventMatcherPolicyForm";
import "@goauthentik/web/pages/policies/expiry/ExpiryPolicyForm";
import "@goauthentik/web/pages/policies/expression/ExpressionPolicyForm";
import "@goauthentik/web/pages/policies/hibp/HaveIBeenPwnedPolicyForm";
import "@goauthentik/web/pages/policies/password/PasswordPolicyForm";
import "@goauthentik/web/pages/policies/reputation/ReputationPolicyForm";
import { groupBy } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

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
        return t`Policies`;
    }
    pageDescription(): string {
        return t`Allow users to use Applications based on properties, enforce Password Criteria and selectively apply Stages.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-infrastructure";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<AKResponse<Policy>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Type`),
            new TableColumn(t`Actions`),
        ];
    }

    groupBy(items: Policy[]): [string, Policy[]][] {
        return groupBy(items, (policy) => policy.verboseNamePlural);
    }

    row(item: Policy): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
                ${(item.boundTo || 0) > 0
                    ? html`<i class="pf-icon pf-icon-ok"></i>
                          <small>${t`Assigned to ${item.boundTo} object(s).`}</small>`
                    : html`<i class="pf-icon pf-icon-warning-triangle"></i>
                          <small>${t`Warning: Policy is not assigned.`}</small>`}
            </div>`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update ${item.verboseName}`} </span>
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
                    <span slot="submit"> ${t`Test`} </span>
                    <span slot="header"> ${t`Test Policy`} </span>
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
            objectLabel=${t`Policy / Policies`}
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-policy-wizard> </ak-policy-wizard>`;
    }

    renderToolbar(): TemplateResult {
        return html` ${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${t`Successfully cleared policy cache`}
                errorMessage=${t`Failed to delete policy cache`}
                action=${t`Clear cache`}
                .onConfirm=${() => {
                    return new PoliciesApi(DEFAULT_CONFIG).policiesAllCacheClearCreate();
                }}
            >
                <span slot="header"> ${t`Clear Policy cache`} </span>
                <p slot="body">
                    ${t`Are you sure you want to clear the policy cache?
                This will cause all policies to be re-evaluated on their next usage.`}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                    ${t`Clear cache`}
                </button>
                <div slot="modal"></div>
            </ak-forms-confirm>`;
    }
}
