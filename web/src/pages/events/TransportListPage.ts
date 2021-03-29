import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ActionButton";
import "../../elements/forms/ModalForm";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { EventsApi, NotificationTransport } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/DeleteForm";
import "./TransportForm";

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
        return "pf-icon pf-icon-export";
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
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Notification Transport")}
                </span>
                <ak-event-transport-form slot="form" .transport=${item}>
                </ak-event-transport-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Notifications Transport")}
                .delete=${() => {
                    return new EventsApi(DEFAULT_CONFIG).eventsTransportsDelete({
                        uuid: item.pk || ""
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
                ${gettext("Create Notification Transport")}
            </span>
            <ak-event-transport-form slot="form">
            </ak-event-transport-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
