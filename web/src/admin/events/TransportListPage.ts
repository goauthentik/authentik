import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/events/TransportForm";
import "#admin/rbac/ObjectPermissionModal";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import {
    EventsApi,
    NotificationTransport,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-event-transport-list")
export class TransportListPage extends TablePage<NotificationTransport> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Notification Transports");
    }
    pageDescription(): string {
        return msg("Define how notifications are sent to users, like Email or Webhook.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-export";
    }

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<NotificationTransport>> {
        return new EventsApi(DEFAULT_CONFIG).eventsTransportsList(
            await this.defaultEndpointConfig(),
        );
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Mode"), "mode"),
            new TableColumn(msg("Actions")),
        ];
    }

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

    row(item: NotificationTransport): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.modeVerbose}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Notification Transport")} </span>
                    <ak-event-transport-form slot="form" .instancePk=${item.pk}>
                    </ak-event-transport-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikEventsNotificationtransport}
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
                </ak-action-button>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Notification Transport")} </span>
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
