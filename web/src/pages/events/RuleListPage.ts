import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/policies/BoundPoliciesList";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/ModalForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { EventsApi, NotificationRule } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";
import "../../elements/forms/DeleteForm";
import "./RuleForm";

@customElement("ak-event-rule-list")
export class RuleListPage extends TablePage<NotificationRule> {
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
        return "pf-icon pf-icon-attention-bell";
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<NotificationRule>> {
        return new EventsApi(DEFAULT_CONFIG).eventsRulesList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
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

    row(item: NotificationRule): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.severity}`,
            html`${item.group?.name || gettext("None (rule disabled)")}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Notification Rule")}
                </span>
                <ak-event-rule-form slot="form" .rule=${item}>
                </ak-event-rule-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Notification rule")}
                .delete=${() => {
                    return new EventsApi(DEFAULT_CONFIG).eventsRulesDelete({
                        pbmUuid: item.pk || ""
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
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Notification Rule")}
            </span>
            <ak-event-rule-form slot="form">
            </ak-event-rule-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }

    renderExpanded(item: NotificationRule): TemplateResult {
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
