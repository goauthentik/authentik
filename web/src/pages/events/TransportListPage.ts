import { t } from "@lingui/macro";
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
        return t`Notification Transports`;
    }
    pageDescription(): string {
        return t`Define how notifications are sent to users, like Email or Webhook.`;
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
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Mode`, "mode"),
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
                ${t`Test`}
            </ak-action-button>
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update Notification Transport`}
                </span>
                <ak-event-transport-form slot="form" .transport=${item}>
                </ak-event-transport-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Notifications Transport`}
                .delete=${() => {
                    return new EventsApi(DEFAULT_CONFIG).eventsTransportsDelete({
                        uuid: item.pk || ""
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
                ${t`Create Notification Transport`}
            </span>
            <ak-event-transport-form slot="form">
            </ak-event-transport-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Create`}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
