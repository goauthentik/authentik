import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/policies/BoundPoliciesList";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { Rule } from "../../api/EventRules";

@customElement("ak-event-rule-list")
export class RuleListPage extends TablePage<Rule> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Notification Rules");
    }
    pageDescription(): string {
        return gettext("Send notifications whenever a specific Event is created and matched by policies.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-attention-bell");
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Rule>> {
        return Rule.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Severity", "severity"),
            new TableColumn("Sent to group", "group"),
            new TableColumn(""),
        ];
    }

    row(item: Rule): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.severity}`,
            html`${item.group?.name || gettext("None (rule disabled)")}`,
            html`
            <ak-modal-button href="${Rule.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Rule.adminUrl(`${item.pk}/delete/`)}">
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
        <ak-modal-button href=${Rule.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }

    renderExpanded(item: Rule): TemplateResult {
        return html`
        <td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <ak-bound-policies-list .target=${item.pk}>
                </ak-bound-policies-list>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }
}
