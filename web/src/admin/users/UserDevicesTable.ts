import "#elements/forms/DeleteBulkForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { deviceTypeName } from "#common/labels";
import { SentryIgnoredError } from "#common/sentry/index";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

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

    protected columns: TableColumn[] = [
        [msg("Name")],
        [msg("Type")],
        [msg("Confirmed")],
        [msg("Created at")],
        [msg("Last updated at")],
        [msg("Last used at")],
    ];

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
            object-label=${msg("Device(s)")}
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

    row(item: Device): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`<div>
                    ${deviceTypeName(item)}
                    ${item.extraDescription ? ` - ${item.extraDescription}` : ""}
                </div>
                ${item.externalId ? html` <small>${item.externalId}</small> ` : nothing} `,
            html`${item.confirmed ? msg("Yes") : msg("No")}`,
            Timestamp(item.created),
            Timestamp(item.lastUpdated),
            Timestamp(item.lastUsed),
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-device-table": UserDeviceTable;
    }
}
