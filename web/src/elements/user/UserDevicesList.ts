import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/forms/DeleteBulkForm";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import {
    MFADevicesPage,
    deviceTypeName,
} from "@goauthentik/web/user/user-settings/mfa/MFADevicesPage";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

@customElement("ak-user-device-list")
export class UserDeviceList extends MFADevicesPage {
    @property({ type: Number })
    userId?: number;

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async apiEndpoint(page: number): Promise<AKResponse<Device>> {
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
            case "otp_totp.TOTPDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAdminTotpDestroy({
                    id: device.pk,
                });
            case "otp_static.StaticDevice":
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
            new TableColumn(t`Name`, ""),
            new TableColumn(t`Type`, ""),
            new TableColumn(t`Confirmed`, ""),
        ];
    }

    renderToolbar(): TemplateResult {
        return html` <ak-spinner-button
            .callAction=${() => {
                return this.fetch();
            }}
            class="pf-m-secondary"
        >
            ${t`Refresh`}</ak-spinner-button
        >`;
    }

    row(item: Device): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${deviceTypeName(item)}`,
            html`${item.confirmed ? t`Yes` : t`No`}`,
        ];
    }
}
