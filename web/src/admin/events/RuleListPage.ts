import "#admin/events/RuleForm";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { severityToLabel } from "#common/labels";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { RuleForm } from "#admin/events/RuleForm";

import { EventsApi, ModelEnum, NotificationRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-event-rule-list")
export class RuleListPage extends TablePage<NotificationRule> {
    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg(
        "Search for a notification rule by name, severity or group...",
    );

    protected override searchEnabled = true;
    public pageTitle = msg("Notification Rules");
    public pageDescription = msg(
        "Send notifications whenever a specific Event is created and matched by policies.",
    );
    public pageIcon = "pf-icon pf-icon-attention-bell";

    @property()
    public order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<NotificationRule>> {
        return new EventsApi(DEFAULT_CONFIG).eventsRulesList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Enabled")],
        [msg("Name"), "name"],
        [msg("Severity"), "severity"],
        [msg("Sent to group"), "group"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Notification rule(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: NotificationRule) => {
                return new EventsApi(DEFAULT_CONFIG).eventsRulesUsedByList({
                    pbmUuid: item.pk,
                });
            }}
            .delete=${(item: NotificationRule) => {
                return new EventsApi(DEFAULT_CONFIG).eventsRulesDestroy({
                    pbmUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: NotificationRule): SlottedTemplateResult[] {
        const enabled = !!item.destinationGroupObj || item.destinationEventUser;
        return [
            html`<ak-status-label ?good=${enabled}></ak-status-label>`,
            html`${item.name}`,
            html`${severityToLabel(item.severity)}`,
            html`${item.destinationGroupObj
                ? html`<a href="#/identity/groups/${item.destinationGroupObj.pk}"
                      >${item.destinationGroupObj.name}</a
                  >`
                : msg("-")}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(RuleForm, item.pk, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikEventsNotificationrule}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(RuleForm);
    }

    protected override renderExpanded(item: NotificationRule): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikEventsNotificationrule.split(".");

        return html`<p>
                ${msg(
                    `These bindings control upon which events this rule triggers.
Bindings to groups/users are checked against the user of the event.`,
                )}
            </p>
            <ak-bound-policies-list .target=${item.pk}> </ak-bound-policies-list>
            <dl class="pf-c-description-list pf-m-horizontal">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Tasks")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <ak-task-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${item.pk}"
                            ></ak-task-list>
                        </div>
                    </dd>
                </div>
            </dl>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-rule-list": RuleListPage;
    }
}
