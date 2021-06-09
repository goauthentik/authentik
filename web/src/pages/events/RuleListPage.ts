import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../policies/BoundPoliciesList";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/ModalForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { EventsApi, NotificationRule } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/DeleteForm";
import "./RuleForm";

@customElement("ak-event-rule-list")
export class RuleListPage extends TablePage<NotificationRule> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Notification Rules`;
    }
    pageDescription(): string {
        return t`Send notifications whenever a specific Event is created and matched by policies.`;
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
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Severity`, "severity"),
            new TableColumn(t`Sent to group`, "group"),
            new TableColumn(""),
        ];
    }

    row(item: NotificationRule): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.severity}`,
            html`${item.groupObj?.name || t`None (rule disabled)`}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update Notification Rule`}
                </span>
                <ak-event-rule-form slot="form" .instancePk=${item.pk}>
                </ak-event-rule-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Notification rule`}
                .usedBy=${() => {
                    return new EventsApi(DEFAULT_CONFIG).eventsRulesUsedByList({
                        pbmUuid: item.pk
                    });
                }}
                .delete=${() => {
                    return new EventsApi(DEFAULT_CONFIG).eventsRulesDestroy({
                        pbmUuid: item.pk
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
        <ak-forms-modal>
            <span slot="submit">
                ${t`Create`}
            </span>
            <span slot="header">
                ${t`Create Notification Rule`}
            </span>
            <ak-event-rule-form slot="form">
            </ak-event-rule-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Create`}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }

    renderExpanded(item: NotificationRule): TemplateResult {
        return html`
        <td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <p>${t`These bindings control upon which events this rule triggers. Bindings to
                groups/users are checked against the user of the event.`}</p>
                <ak-bound-policies-list .target=${item.pk}>
                </ak-bound-policies-list>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }
}
