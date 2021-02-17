import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { DefaultClient, AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ActionButton";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { Transport } from "../../api/EventTransports";

@customElement("ak-event-transport-list")
export class TransportListPage extends TablePage<Transport> {
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

    apiEndpoint(page: number): Promise<AKResponse<Transport>> {
        return Transport.list({
            ordering: this.order,
            page: page,
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

    row(item: Transport): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.mode_verbose}`,
            html`
            <ak-action-button url="${DefaultClient.makeUrl(["events", "transports", item.pk,  "test"])}">
                ${gettext("Test")}
            </ak-action-button>
            <ak-modal-button href="${Transport.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Transport.adminUrl(`${item.pk}/delete/`)}">
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
        <ak-modal-button href=${Transport.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
