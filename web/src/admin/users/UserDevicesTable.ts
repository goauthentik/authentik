import { deviceTypeName } from "@goauthentik/common/labels";
import {
    destroyAuthenticatorDevice,
    retrieveAuthenticatorsAdminAllList,
} from "@goauthentik/connectors/authenticators";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Device } from "@goauthentik/api";

@customElement("ak-user-device-table")
export class UserDeviceTable extends Table<Device> {
    @property({ type: Number })
    userId?: number;

    checkbox = true;

    async apiEndpoint(): Promise<PaginatedResponse<Device>> {
        if (!this.userId) {
            throw new Error(`Attempted to retrieve authenticator list for undefined user`);
        }
        const results = await retrieveAuthenticatorsAdminAllList(this.userId);
        return {
            pagination: {
                count: results.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: results.length,
                next: 0,
                previous: 0,
            },
            results,
        };
    }

    columns(): TableColumn[] {
        // prettier-ignore
        return [
            msg("Name"),
            msg("Type"),
            msg("Confirmed")
        ].map((th) => new TableColumn(th, ""));
    }

    async deleteWrapper(device: Device) {
        return destroyAuthenticatorDevice(device.type, device.pk);
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Device(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: Device) => {
                return this.deleteWrapper(item);
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderToolbar(): TemplateResult {
        return html` <ak-spinner-button
            .callAction=${() => {
                return this.fetch();
            }}
            class="pf-m-secondary"
        >
            ${msg("Refresh")}</ak-spinner-button
        >`;
    }

    row(item: Device): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${deviceTypeName(item)}`,
            html`${item.confirmed ? msg("Yes") : msg("No")}`,
        ];
    }
}
