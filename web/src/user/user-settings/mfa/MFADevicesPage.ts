import { AndNext, DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/TokenCopyButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";
import "@goauthentik/user/user-settings/mfa/MFADeviceForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { AuthenticatorsApi, Device, UserSetting } from "@goauthentik/api";

export function stageToAuthenticatorName(stage: UserSetting): string {
    switch (stage.component) {
        case "ak-user-settings-authenticator-duo":
            return msg("Duo authenticator");
        case "ak-user-settings-authenticator-sms":
            return msg("SMS authenticator");
        case "ak-user-settings-authenticator-static":
            return msg("Static authenticator");
        case "ak-user-settings-authenticator-totp":
            return msg("TOTP authenticator");
        case "ak-user-settings-authenticator-webauthn":
            return msg("Security key authenticator");
    }
    return `Invalid stage component ${stage.component}`;
}

export function deviceTypeName(device: Device): string {
    switch (device.type) {
        case "otp_static.StaticDevice":
            return msg("Static tokens");
        case "otp_totp.TOTPDevice":
            return msg("TOTP Device");
        default:
            return device.verboseName;
    }
}

@customElement("ak-user-settings-mfa")
export class MFADevicesPage extends Table<Device> {
    @property({ attribute: false })
    userSettings?: Promise<UserSetting[]>;

    checkbox = true;

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async apiEndpoint(page: number): Promise<PaginatedResponse<Device>> {
        const devices = await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAllList();
        return {
            pagination: {
                current: 0,
                count: devices.length,
                totalPages: 1,
                startIndex: 1,
                endIndex: devices.length,
            },
            results: devices,
        };
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("Type")), new TableColumn("")];
    }

    renderToolbar(): TemplateResult {
        return html`<ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${msg("Enroll")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(
                        this.userSettings?.then((stages) => {
                            return stages
                                .filter((stage) => {
                                    if (stage.component === "ak-user-settings-password") {
                                        return false;
                                    }
                                    return stage.configureUrl;
                                })
                                .map((stage) => {
                                    return html`<li>
                                        <a
                                            href="${ifDefined(stage.configureUrl)}${AndNext(
                                                `/if/user/#/settings;${JSON.stringify({
                                                    page: "page-mfa",
                                                })}`,
                                            )}"
                                            class="pf-c-dropdown__menu-item"
                                        >
                                            ${stageToAuthenticatorName(stage)}
                                        </a>
                                    </li>`;
                                });
                        }),
                        html`<ak-empty-state
                            ?loading="${true}"
                            header=${msg("Loading")}
                        ></ak-empty-state>`,
                    )}
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}`;
    }

    async deleteWrapper(device: Device) {
        switch (device.type) {
            case "authentik_stages_authenticator_duo.DuoDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsDuoDestroy({
                    id: device.pk,
                });
            case "authentik_stages_authenticator_sms.SMSDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsSmsDestroy({
                    id: device.pk,
                });
            case "otp_totp.TOTPDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsTotpDestroy({
                    id: device.pk,
                });
            case "otp_static.StaticDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsStaticDestroy({
                    id: device.pk,
                });
            case "authentik_stages_authenticator_webauthn.WebAuthnDevice":
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsWebauthnDestroy({
                    id: device.pk,
                });
            default:
                break;
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

    row(item: Device): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${deviceTypeName(item)}`,
            html`
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Device")}</span>
                    <ak-user-mfa-form slot="form" deviceType=${item.type} .instancePk=${item.pk}>
                    </ak-user-mfa-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
            `,
        ];
    }
}
