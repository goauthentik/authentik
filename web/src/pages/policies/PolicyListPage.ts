import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import "./PolicyTestForm";
import { TableColumn } from "../../elements/table/Table";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";
import { PoliciesApi, Policy } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "./dummy/DummyPolicyForm";
import "./event_matcher/EventMatcherPolicyForm";
import "./expression/ExpressionPolicyForm";
import "./expiry/ExpiryPolicyForm";
import "./hibp/HaveIBeenPwnedPolicyForm";
import "./password/PasswordPolicyForm";
import "./reputation/ReputationPolicyForm";

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

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Policy>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Type`),
            new TableColumn(""),
        ];
    }

    row(item: Policy): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
                ${(item.boundTo || 0) > 0 ?
                        html`<i class="pf-icon pf-icon-ok"></i>
                        <small>
                            ${t`Assigned to ${item.boundTo} objects.`}
                        </small>`:
                    html`<i class="pf-icon pf-icon-warning-triangle"></i>
                    <small>${t`Warning: Policy is not assigned.`}</small>`}
            </div>`,
            html`${item.verboseName}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update ${item.verboseName}`}
                </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        "policyUUID": item.pk
                    }}
                    type=${ifDefined(item.component)}>
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">
                    ${t`Test`}
                </span>
                <span slot="header">
                    ${t`Test Policy`}
                </span>
                <ak-policy-test-form slot="form" .policy=${item}>
                </ak-policy-test-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Test`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Policy`}
                .delete=${() => {
                    return new PoliciesApi(DEFAULT_CONFIG).policiesAllDelete({
                        policyUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete`}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${t`Create`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(new PoliciesApi(DEFAULT_CONFIG).policiesAllTypes().then((types) => {
                        return types.map((type) => {
                            return html`<li>
                                <ak-forms-modal>
                                    <span slot="submit">
                                        ${t`Create`}
                                    </span>
                                    <span slot="header">
                                        ${t`Create ${type.name}`}
                                    </span>
                                    <ak-proxy-form
                                        slot="form"
                                        type=${type.component}>
                                    </ak-proxy-form>
                                    <button slot="trigger" class="pf-c-dropdown__menu-item">
                                        ${type.name}<br>
                                        <small>${type.description}</small>
                                    </button>
                                </ak-forms-modal>
                            </li>`;
                        });
                    }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        ${super.renderToolbar()}`;
    }

}
