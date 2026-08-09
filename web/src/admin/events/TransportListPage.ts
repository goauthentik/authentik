/**
 * @file Display the table of available Notification Transports, with pending tasks for each
 */

import "#admin/events/TransportForm";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { taskCard } from "#components/tasks/taskCard";

import { TransportForm } from "#admin/events/TransportForm";

import { EventsApi, ModelEnum, NotificationTransport } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

const NOTIFICATION_MODEL = ModelEnum.AuthentikEventsNotificationtransport;

@customElement("ak-event-transport-list")
export class TransportListPage extends TablePage<NotificationTransport> {
    protected override searchEnabled = true;
    public pageTitle = msg("Notification Transports");
    public pageDescription = msg(
        "Define how notifications are sent to users, like Email or Webhook.",
    );
    public pageIcon = "pf-icon pf-icon-export";

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;
    public override searchPlaceholder = msg(
        "Search for a notification transport by name or mode...",
    );

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<NotificationTransport>> {
        return aki(EventsApi).eventsTransportsList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Mode"), "mode"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Notification transport(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: NotificationTransport) => {
                return aki(EventsApi).eventsTransportsUsedByList({
                    uuid: item.pk,
                });
            }}
            .delete=${(item: NotificationTransport) => {
                return aki(EventsApi).eventsTransportsDestroy({
                    uuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: NotificationTransport): SlottedTemplateResult[] {
        return [
            item.name,
            item.modeVerbose,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(TransportForm, item.pk, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikEventsNotificationtransport}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
                <ak-action-button
                    class="pf-m-plain"
                    .apiRequest=${() => {
                        return aki(EventsApi).eventsTransportsTestCreate({
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

    protected override renderExpanded(item: NotificationTransport): SlottedTemplateResult {
        return taskCard(NOTIFICATION_MODEL, item.pk);
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(TransportForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-transport-list": TransportListPage;
    }
}
