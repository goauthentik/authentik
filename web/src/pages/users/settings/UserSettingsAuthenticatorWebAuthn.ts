import { CSSResult, customElement, html, TemplateResult } from "lit-element";
import { gettext } from "django";
import { AuthenticatorsApi, StagesApi, WebAuthnDevice } from "authentik-api";
import { until } from "lit-html/directives/until";
import { FlowURLManager } from "../../../api/legacy";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { BaseUserSettings } from "./BaseUserSettings";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";
import "../../../elements/forms/Form";
import "../../../elements/forms/ModalForm";

@customElement("ak-user-settings-authenticator-webauthn")
export class UserSettingsAuthenticatorWebAuthn extends BaseUserSettings {

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDataList);
    }

    renderDelete(device: WebAuthnDevice): TemplateResult {
        return html`<ak-forms-delete
            .obj=${device}
            objectLabel=${gettext("Authenticator")}
            .delete=${() => {
                return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsWebauthnDelete({
                    id: device.pk || 0
                });
            }}>
            <button slot="trigger" class="pf-c-button pf-m-danger">
                ${gettext("Delete")}
            </button>
        </ak-forms-delete>`;
    }

    renderUpdate(device: WebAuthnDevice): TemplateResult {
        return html`<ak-forms-modal>
            <span slot="submit">
                ${gettext("Update")}
            </span>
            <span slot="header">
                ${gettext("Update")}
            </span>
            <ak-form
                slot="form"
                successMessage=${gettext("Successfully updated device.")}
                .send=${(data: unknown) => {
                    return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsWebauthnUpdate({
                        id: device.pk || 0,
                        data: data as WebAuthnDevice
                    });
                }}>
                <form class="pf-c-form pf-m-horizontal">
                    <paper-input
                        name="name"
                        ?alwaysFloatLabel=${true}
                        label="${gettext("Device name")}"
                        value=${device.name}>
                    </paper-input>
                </form>
            </ak-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Update")}
            </button>
        </ak-forms-modal>`;
    }

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
                                            ${this.renderUpdate(device)}
                                            ${this.renderDelete(device)}
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
