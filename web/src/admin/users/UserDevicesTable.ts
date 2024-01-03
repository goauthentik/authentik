import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { deviceTypeName } from "@goauthentik/common/labels";
import { getRelativeTime } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

@customElement("ak-user-device-table")
export class UserDeviceTable extends Table<Device> {
    @property({ type: Number })
    userId?: number;

    checkbox = true;
    clearOnRefresh = true;
    expandable = true;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

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
        switch (device.type.toLowerCase()) {
            case "authentik_stages_authenticator_duo.duodevice":
                return api.authenticatorsAdminDuoDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_sms.smsdevice":
                return api.authenticatorsAdminSmsDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_totp.totpdevice":
                return api.authenticatorsAdminTotpDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_static.staticdevice":
                return api.authenticatorsAdminStaticDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_webauthn.webauthndevice":
                return api.authenticatorsAdminWebauthnDestroy({ id: parseInt(device.pk, 10) });
            case "authentik_stages_authenticator_mobile.mobiledevice":
                return api.authenticatorsMobileDestroy({
                    uuid: device.pk,
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

    renderExpanded(item: Device): TemplateResult {
        return html`
            <td role="cell" colspan="5">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        ${until(
                            new AuthenticatorsApi(DEFAULT_CONFIG)
                                .authenticatorsMobileRetrieve({
                                    uuid: item.pk,
                                })
                                .then((device) => {
                                    return html`
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${msg("Last check-in")}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${device.lastCheckin.toLocaleString()}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${msg("App version")}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${device.state.appVersion}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${msg("Device model")}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${device.state.model}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${msg("OS Version")}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${device.state.osVersion}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${msg("Platform")}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${device.state.platform}
                                                </div>
                                            </dd>
                                        </div>
                                    `;
                                }),
                        )}
                    </dl>
                </div>
            </td>
        `;
    }

    rowExpandable(item: Device): boolean {
        return item.type.toLowerCase() === "authentik_stages_authenticator_mobile.mobiledevice";
    }

    row(item: Device): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${deviceTypeName(item)}`,
            html`${item.confirmed ? msg("Yes") : msg("No")}`,
            html`<div>${getRelativeTime(item.created)}</div>
                <small>${item.created.toLocaleString()}</small>`,
            html`<div>${getRelativeTime(item.lastUpdated)}</div>
                <small>${item.lastUpdated.toLocaleString()}</small>`,
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
