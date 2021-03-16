import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ActionButton";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { EventsApi, NotificationTransport } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

@customElement("ak-event-transport-list")
export class TransportListPage extends TablePage<NotificationTransport> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Notification Transports");
    }
    pageDescription(): string {
        return gettext("Define how notifications are sent to users, like Email or Webhook.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-export");
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<NotificationTransport>> {
        return new EventsApi(DEFAULT_CONFIG).eventsTransportsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Mode", "mode"),
            new TableColumn(""),
        ];
    }

    row(item: NotificationTransport): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.modeVerbose}`,
            html`
            <ak-action-button
                .apiRequest=${() => {
                    return new EventsApi(DEFAULT_CONFIG).eventsTransportsTest({
                        uuid: item.pk || "",
                    });
                }}>
                ${gettext("Test")}
            </ak-action-button>
            <ak-modal-button href="${AdminURLManager.eventTransports(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${AdminURLManager.eventTransports(`${item.pk}/delete/`)}">
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
        <ak-modal-button href=${AdminURLManager.eventTransports("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
