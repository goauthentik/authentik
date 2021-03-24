import { customElement, html, TemplateResult } from "lit-element";
import { gettext } from "django";
import { AuthenticatorsApi, StagesApi } from "authentik-api";
import { until } from "lit-html/directives/until";
import { FlowURLManager, UserURLManager } from "../../../api/legacy";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { BaseUserSettings } from "./BaseUserSettings";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";

@customElement("ak-user-settings-authenticator-webauthn")
export class UserSettingsAuthenticatorWebAuthnDevices extends BaseUserSettings {

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${gettext("WebAuthn Devices")}
            </div>
            <div class="pf-c-card__body">
                <ul class="pf-c-data-list" role="list">
                    ${until(new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsWebauthnList({}).then((devices) => {
                        return devices.results.map((device) => {
                            return html`<li class="pf-c-data-list__item">
                                <div class="pf-c-data-list__item-row">
                                    <div class="pf-c-data-list__item-content">
                                        <div class="pf-c-data-list__cell">${device.name || "-"}</div>
                                        <div class="pf-c-data-list__cell">
                                            ${gettext(`Created ${device.createdOn?.toLocaleString()}`)}
                                        </div>
                                        <div class="pf-c-data-list__cell">
                                            <ak-modal-button href="${UserURLManager.authenticatorWebauthn(`devices/${device.pk}/update/`)}">
                                                <ak-spinner-button slot="trigger" class="pf-m-primary">
                                                    ${gettext("Update")}
                                                </ak-spinner-button>
                                                <div slot="modal"></div>
                                            </ak-modal-button>
                                            <ak-forms-delete
                                                .obj=${device}
                                                objectLabel=${gettext("Authenticator")}
                                                .delete=${() => {
                                                    return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsWebauthnDelete({
                                                        id: device.pk || 0
                                                    });
                                                }}>
                                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                                    ${gettext("Delete")}
                                                </button>
                                            </ak-forms-delete>
                                        </div>
                                    </div>
                                </div>
                            </li>`;
                        });
                    }))}
                </ul>
            </div>
            <div class="pf-c-card__footer">
                ${until(new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnRead({ stageUuid: this.objectId}).then((stage) => {
                    if (stage.configureFlow) {
                        return html`<a href="${FlowURLManager.configure(stage.pk || "", "?next=/%23%2Fuser")}"
                                class="pf-c-button pf-m-primary">${gettext("Configure WebAuthn")}
                            </a>`;
                    }
                    return html``;
                }))}
            </div>
        </div>`;
    }

}
