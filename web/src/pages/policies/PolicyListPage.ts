import { gettext } from "django";
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

@customElement("ak-policy-list")
export class PolicyListPage extends TablePage<Policy> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Policies");
    }
    pageDescription(): string {
        return gettext("Allow users to use Applications based on properties, enforce Password Criteria and selectively apply Stages.");
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
            new TableColumn("Name", "name"),
            new TableColumn("Type"),
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
                            ${gettext(`Assigned to ${item.boundTo} objects.`)}
                        </small>`:
                    html`<i class="pf-icon pf-icon-warning-triangle"></i>
                    <small>${gettext("Warning: Policy is not assigned.")}</small>`}
            </div>`,
            html`${item.verboseName}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext(`Update ${item.verboseName}`)}
                </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        "policyUUID": item.pk
                    }}
                    type=${ifDefined(item.objectType)}
                    .typeMap=${{
                        "dummy": "ak-policy-dummy-form",
                        "eventmatcher": "ak-policy-event-matcher-form",
                        "expression": "ak-policy-expression-form",
                    }}>
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">
                    ${gettext("Test")}
                </span>
                <span slot="header">
                    ${gettext("Test Policy")}
                </span>
                <ak-policy-test-form slot="form" .policy=${item}>
                </ak-policy-test-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Test")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Policy")}
                .delete=${() => {
                    return new PoliciesApi(DEFAULT_CONFIG).policiesAllDelete({
                        policyUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${gettext("Create")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(new PoliciesApi(DEFAULT_CONFIG).policiesAllTypes().then((types) => {
                        return types.map((type) => {
                            return html`<li>
                                <ak-forms-modal>
                                    <span slot="submit">
                                        ${gettext("Create")}
                                    </span>
                                    <span slot="header">
                                        ${gettext(`Create ${type.name}`)}
                                    </span>
                                    <ak-proxy-form
                                        slot="form"
                                        type=${type.link}>
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
