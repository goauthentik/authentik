import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/TokenCopyButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#user/user-settings/mfa/MFADeviceForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AndNext, DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";
import { deviceTypeName } from "#common/labels";
import { SentryIgnoredError } from "#common/sentry/index";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { AuthenticatorsApi, Device, UserSetting } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export const stageToAuthenticatorName = (stage: UserSetting) =>
    stage.title ?? `Invalid stage component ${stage.component}`;

@customElement("ak-user-settings-mfa")
export class MFADevicesPage extends Table<Device> {
    @property({ attribute: false })
    userSettings?: UserSetting[];

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<Device>> {
        const devices = await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAllList();
        return {
            pagination: {
                current: 0,
                count: devices.length,
                totalPages: 1,
                startIndex: 1,
                endIndex: devices.length,
                next: 0,
                previous: 0,
            },
            results: devices,
        };
    }

    columns(): TableColumn[] {
        // prettier-ignore
        return [
            msg("Name"),
            msg("Type"),
            msg("Created at"),
            msg("Last used at"),
            ""
        ].map((th) => new TableColumn(th, ""));
    }

    renderToolbar(): TemplateResult {
        const settings = (this.userSettings || []).filter((stage) => {
            if (stage.component === "ak-user-settings-password") {
                return false;
            }
            return stage.configureUrl;
        });
        return html`<ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${msg("Enroll")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${settings.map((stage) => {
                        return html`<li>
                            <a
                                href="${ifDefined(stage.configureUrl)}${AndNext(
                                    `${globalAK().api.relBase}if/user/#/settings;${JSON.stringify({
                                        page: "page-mfa",
                                    })}`,
                                )}"
                                class="pf-c-dropdown__menu-item"
                            >
                                ${stageToAuthenticatorName(stage)}
                            </a>
                        </li>`;
                    })}
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}`;
    }

    async deleteWrapper(device: Device) {
        const api = new AuthenticatorsApi(DEFAULT_CONFIG);
        const id = { id: parseInt(device.pk, 10) };
        switch (device.type) {
            case "authentik_stages_authenticator_duo.DuoDevice":
                return api.authenticatorsDuoDestroy(id);
            case "authentik_stages_authenticator_email.EmailDevice":
                return api.authenticatorsEmailDestroy(id);
            case "authentik_stages_authenticator_sms.SMSDevice":
                return api.authenticatorsSmsDestroy(id);
            case "authentik_stages_authenticator_totp.TOTPDevice":
                return api.authenticatorsTotpDestroy(id);
            case "authentik_stages_authenticator_static.StaticDevice":
                return api.authenticatorsStaticDestroy(id);
            case "authentik_stages_authenticator_webauthn.WebAuthnDevice":
                return api.authenticatorsWebauthnDestroy(id);
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

    row(item: Device): TemplateResult[] {
        return [
            html`${item.name}`,
            html`<div>${deviceTypeName(item)}</div>
                ${item.extraDescription
                    ? html`
                          <pf-tooltip position="top" content=${item.externalId || ""}>
                              <small>${item.extraDescription}</small>
                          </pf-tooltip>
                      `
                    : nothing} `,
            html`${item.created.getTime() > 0
                ? html`<div>${formatElapsedTime(item.created)}</div>
                      <small>${item.created.toLocaleString()}</small>`
                : html`-`}`,
            html`${item.lastUsed
                ? html`<div>${formatElapsedTime(item.lastUsed)}</div>
                      <small>${item.lastUsed.toLocaleString()}</small>`
                : html`-`}`,
            html`
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Device")}</span>
                    <ak-user-mfa-form slot="form" deviceType=${item.type} .instancePk=${item.pk}>
                    </ak-user-mfa-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
            `,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-mfa": MFADevicesPage;
    }
}
