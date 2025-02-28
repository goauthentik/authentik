import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { SentryIgnoredError } from "@goauthentik/common/errors.js";
import { deviceTypeName } from "@goauthentik/common/labels.js";
import { getRelativeTime } from "@goauthentik/common/utils.js";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

@customElement("ak-user-device-table")
export class UserDeviceTable extends Table<Device> {
    @property({ type: Number })
    userId?: number;

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<Device>> {
        return new AuthenticatorsApi(DEFAULT_CONFIG)
            .authenticatorsAdminAllList({
                user: this.userId,
            })
            .then((res) => {
                return {
                    pagination: {
                        count: res.length,
                        current: 1,
                        totalPages: 1,
                        startIndex: 1,
                        endIndex: res.length,
                        next: 0,
                        previous: 0,
                    },
                    results: res,
                };
            });
    }

    columns(): TableColumn[] {
        // prettier-ignore
        return [
            msg("Name"),
            msg("Type"),
            msg("Confirmed"),
            msg("Created at"),
            msg("Last updated at"),
            msg("Last used at"),
        ].map((th) => new TableColumn(th, ""));
    }

    async deleteWrapper(device: Device) {
        const api = new AuthenticatorsApi(DEFAULT_CONFIG);
        switch (device.type) {
            case "authentik_stages_authenticator_duo.DuoDevice":
                return api.authenticatorsAdminDuoDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_email.EmailDevice":
                return api.authenticatorsAdminEmailDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_sms.SMSDevice":
                return api.authenticatorsAdminSmsDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_totp.TOTPDevice":
                return api.authenticatorsAdminTotpDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_static.StaticDevice":
                return api.authenticatorsAdminStaticDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_webauthn.WebAuthnDevice":
                return api.authenticatorsAdminWebauthnDestroy({ id: parseInt(device.pk, 10) });
            default:
                throw new SentryIgnoredError(
                    msg(str`Device type ${device.verboseName} cannot be deleted`),
                );
        }
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
            html`${deviceTypeName(item)}
            ${item.extraDescription ? ` - ${item.extraDescription}` : ""}`,
            html`${item.confirmed ? msg("Yes") : msg("No")}`,
            html`${item.created.getTime() > 0
                ? html`<div>${getRelativeTime(item.created)}</div>
                      <small>${item.created.toLocaleString()}</small>`
                : html`-`}`,
            html`${item.lastUpdated
                ? html`<div>${getRelativeTime(item.lastUpdated)}</div>
                      <small>${item.lastUpdated.toLocaleString()}</small>`
                : html`-`}`,
            html`${item.lastUsed
                ? html`<div>${getRelativeTime(item.lastUsed)}</div>
                      <small>${item.lastUsed.toLocaleString()}</small>`
                : html`-`}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-device-table": UserDeviceTable;
    }
}
