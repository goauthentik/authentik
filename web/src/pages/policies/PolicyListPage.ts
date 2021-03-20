import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import { TableColumn } from "../../elements/table/Table";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";
import { PoliciesApi, Policy } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

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
            <ak-modal-button href="${AdminURLManager.policies(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${AdminURLManager.policies(`${item.pk}/test/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Test")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
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
                    ${until(new PoliciesApi(DEFAULT_CONFIG).policiesAllTypes({}).then((types) => {
                        return types.map((type) => {
                            return html`<li>
                                <ak-modal-button href="${type.link}">
                                    <button slot="trigger" class="pf-c-dropdown__menu-item">${type.name}<br>
                                        <small>${type.description}</small>
                                    </button>
                                    <div slot="modal"></div>
                                </ak-modal-button>
                            </li>`;
                        });
                    }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        ${super.renderToolbar()}`;
    }

}
