import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { MFADevicesPage, deviceTypeName } from "@goauthentik/user/user-settings/mfa/MFADevicesPage";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

@customElement("ak-user-device-list")
export class UserDeviceList extends MFADevicesPage {
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

    async deleteWrapper(device: Device) {
        switch (device.type) {
            case "authentik_stages_authenticator_duo.DuoDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAdminDuoDestroy({
                    id: device.pk,
                });
            case "authentik_stages_authenticator_sms.SMSDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAdminSmsDestroy({
                    id: device.pk,
                });
            case "authentik_stages_authenticator_totp.TOTPDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAdminTotpDestroy({
                    id: device.pk,
                });
            case "authentik_stages_authenticator_static.StaticDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAdminStaticDestroy({
                    id: device.pk,
                });
            case "authentik_stages_authenticator_webauthn.WebAuthnDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAdminWebauthnDestroy({
                    id: device.pk,
                });
            default:
                break;
        }
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), ""),
            new TableColumn(msg("Type"), ""),
            new TableColumn(msg("Confirmed"), ""),
        ];
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
