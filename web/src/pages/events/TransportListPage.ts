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

    checkbox = true;

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
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length !== 1;
        const item = this.selectedElements[0];
        return html`<ak-forms-delete
            .obj=${item}
            objectLabel=${t`Notifications Transport`}
            .usedBy=${() => {
                return new EventsApi(DEFAULT_CONFIG).eventsTransportsUsedByList({
                    uuid: item.pk,
                });
            }}
            .delete=${() => {
                return new EventsApi(DEFAULT_CONFIG).eventsTransportsDestroy({
                    uuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete>`;
    }

    row(item: NotificationTransport): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.modeVerbose}`,
            html` <ak-action-button
                    .apiRequest=${() => {
                        return new EventsApi(DEFAULT_CONFIG).eventsTransportsTestCreate({
                            uuid: item.pk || "",
                        });
                    }}
                >
                    ${t`Test`}
                </ak-action-button>
                <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Notification Transport`} </span>
                    <ak-event-transport-form slot="form" .instancePk=${item.pk}>
                    </ak-event-transport-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Notification Transport`} </span>
                <ak-event-transport-form slot="form"> </ak-event-transport-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
