import "#admin/events/TransportForm";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    EventsApi,
    ModelEnum,
    NotificationTransport,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-event-transport-list")
export class TransportListPage extends TablePage<NotificationTransport> {
    protected override searchEnabled = true;
    public pageTitle = msg("Notification Transports");
    public pageDescription = msg(
        "Define how notifications are sent to users, like Email or Webhook.",
    );
    public pageIcon = "pf-icon pf-icon-export";

    checkbox = true;
    clearOnRefresh = true;
    expandable = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<NotificationTransport>> {
        return new EventsApi(DEFAULT_CONFIG).eventsTransportsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Mode"), "mode"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Notification transport(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: NotificationTransport) => {
                return new EventsApi(DEFAULT_CONFIG).eventsTransportsUsedByList({
                    uuid: item.pk,
                });
            }}
            .delete=${(item: NotificationTransport) => {
                return new EventsApi(DEFAULT_CONFIG).eventsTransportsDestroy({
                    uuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: NotificationTransport): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.modeVerbose}`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Notification Transport")}</span>
                    <ak-event-transport-form slot="form" .instancePk=${item.pk}>
                    </ak-event-transport-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikEventsNotificationtransport}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
                <ak-action-button
                    class="pf-m-plain"
                    .apiRequest=${() => {
                        return new EventsApi(DEFAULT_CONFIG).eventsTransportsTestCreate({
                            uuid: item.pk || "",
                        });
                    }}
                >
                    <pf-tooltip position="top" content=${msg("Test")}>
                        <i class="fas fa-vial" aria-hidden="true"></i>
                    </pf-tooltip>
                </ak-action-button>
            </div>`,
        ];
    }

    renderExpanded(item: NotificationTransport): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikEventsNotificationtransport.split(".");
        return html`<dl class="pf-c-description-list pf-m-horizontal">
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

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Notification Transport")}</span>
                <ak-event-transport-form slot="form"> </ak-event-transport-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-transport-list": TransportListPage;
    }
}
