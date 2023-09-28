import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { deviceTypeName } from "@goauthentik/common/labels";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

@customElement("ak-user-device-list")
export class UserDeviceList extends Table<Device> {
    @property({ type: Number })
    userId?: number;

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
            msg("Confirmed")
        ].map((th) => new TableColumn(th, ""));
    }

    async deleteWrapper(device: Device) {
        const api = new AuthenticatorsApi(DEFAULT_CONFIG);
        const id = { id: device.pk };
        switch (device.type) {
            case "authentik_stages_authenticator_duo.DuoDevice":
                return api.authenticatorsAdminDuoDestroy(id);
            case "authentik_stages_authenticator_sms.SMSDevice":
                return api.authenticatorsAdminSmsDestroy(id);
            case "authentik_stages_authenticator_totp.TOTPDevice":
                return api.authenticatorsAdminTotpDestroy(id);
            case "authentik_stages_authenticator_static.StaticDevice":
                return api.authenticatorsAdminStaticDestroy(id);
            case "authentik_stages_authenticator_webauthn.WebAuthnDevice":
                return api.authenticatorsAdminWebauthnDestroy(id);
            default:
                break;
        }
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
