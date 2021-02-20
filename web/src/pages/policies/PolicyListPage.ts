import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { Policy } from "../../api/Policies";
import { until } from "lit-html/directives/until";

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
        return gettext("pf-icon pf-icon-infrastructure");
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Policy>> {
        return Policy.list({
            ordering: this.order,
        page: page,
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
                ${item.bound_to > 0 ?
                        html`<i class="pf-icon pf-icon-ok"></i>
                        <small>
                            ${gettext(`Assigned to ${item.bound_to} objects.`)}
                        </small>`:
                    html`<i class="pf-icon pf-icon-warning-triangle"></i>
                    <small>${gettext("Warning: Policy is not assigned.")}</small>`}
            </div>`,
            html`${item.verbose_name}`,
            html`
            <ak-modal-button href="${Policy.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Policy.adminUrl(`${item.pk}/test/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Test")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Policy.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
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
                    ${until(Policy.getTypes().then((types) => {
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
