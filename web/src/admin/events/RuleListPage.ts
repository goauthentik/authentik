import "@goauthentik/admin/events/RuleForm";
import "@goauthentik/admin/policies/BoundPoliciesList";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import "@goauthentik/admin/system-tasks/TaskList";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { severityToLabel } from "@goauthentik/common/labels";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
    EventsApi,
    ModelEnum,
    NotificationRule,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

@customElement("ak-event-rule-list")
export class RuleListPage extends TablePage<NotificationRule> {
    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Notification Rules");
    }
    pageDescription(): string {
        return msg(
            "Send notifications whenever a specific Event is created and matched by policies.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-attention-bell";
    }

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<NotificationRule>> {
        return new EventsApi(DEFAULT_CONFIG).eventsRulesList(await this.defaultEndpointConfig());
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Enabled")),
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Severity"), "severity"),
            new TableColumn(msg("Sent to group"), "group"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Notification rule(s)")}
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

    row(item: NotificationRule): TemplateResult[] {
        const enabled = !!item.destinationGroupObj || item.destinationEventUser;
        return [
            html`<ak-status-label type="warning" ?good=${enabled}></ak-status-label>`,
            html`${item.name}`,
            html`${severityToLabel(item.severity)}`,
            html`${item.destinationGroupObj
                ? html`<a href="#/identity/groups/${item.destinationGroupObj.pk}"
                      >${item.destinationGroupObj.name}</a
                  >`
                : msg("-")}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Notification Rule")} </span>
                    <ak-event-rule-form slot="form" .instancePk=${item.pk}> </ak-event-rule-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikEventsNotificationrule}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Notification Rule")} </span>
                <ak-event-rule-form slot="form"> </ak-event-rule-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }

    renderExpanded(item: NotificationRule): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikEventsNotificationrule.split(".");
        return html` <td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <p>
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
                </dl>
            </div>
        </td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-rule-list": RuleListPage;
    }
}
