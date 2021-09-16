import { CSSResult, customElement, html, TemplateResult } from "lit-element";
import { t } from "@lingui/macro";
import { AuthenticatorsApi, WebAuthnDevice } from "@goauthentik/api";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { BaseUserSettings } from "../BaseUserSettings";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";
import "../../../elements/forms/Form";
import "../../../elements/forms/ModalForm";
import "../../../elements/forms/HorizontalFormElement";
import { ifDefined } from "lit-html/directives/if-defined";
import { EVENT_REFRESH } from "../../../constants";

@customElement("ak-user-settings-authenticator-webauthn")
export class UserSettingsAuthenticatorWebAuthn extends BaseUserSettings {
    static get styles(): CSSResult[] {
        return super.styles.concat(PFDataList);
    }

    renderDelete(device: WebAuthnDevice): TemplateResult {
        return html`<ak-forms-delete
            .obj=${device}
            objectLabel=${t`Authenticator`}
            .delete=${() => {
                return new AuthenticatorsApi(DEFAULT_CONFIG)
                    .authenticatorsWebauthnDestroy({
                        id: device.pk || 0,
                    })
                    .then(() => {
                        this.dispatchEvent(
                            new CustomEvent(EVENT_REFRESH, {
                                bubbles: true,
                                composed: true,
                            }),
                        );
                    });
            }}
        >
            <button slot="trigger" class="pf-c-button pf-m-danger">${t`Delete`}</button>
        </ak-forms-delete>`;
    }

    renderUpdate(device: WebAuthnDevice): TemplateResult {
        return html`<ak-forms-modal>
            <span slot="submit"> ${t`Update`} </span>
            <span slot="header"> ${t`Update`} </span>
            <ak-form
                slot="form"
                successMessage=${t`Successfully updated device.`}
                .send=${(data: unknown) => {
                    return new AuthenticatorsApi(DEFAULT_CONFIG)
                        .authenticatorsWebauthnUpdate({
                            id: device.pk || 0,
                            webAuthnDeviceRequest: data as WebAuthnDevice,
                        })
                        .then(() => {
                            this.requestUpdate();
                        });
                }}
            >
                <form class="pf-c-form pf-m-horizontal">
                    <ak-form-element-horizontal
                        label=${t`Device name`}
                        ?required=${true}
                        name="name"
                    >
                        <input
                            type="text"
                            value="${ifDefined(device.name)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </form>
            </ak-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${t`Update`}</button>
        </ak-forms-modal>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${t`WebAuthn Devices`}</div>
            <div class="pf-c-card__body">
                <ul class="pf-c-data-list" role="list">
                    ${until(
                        new AuthenticatorsApi(DEFAULT_CONFIG)
                            .authenticatorsWebauthnList({})
                            .then((devices) => {
                                return devices.results.map((device) => {
                                    return html`<li class="pf-c-data-list__item">
                                        <div class="pf-c-data-list__item-row">
                                            <div class="pf-c-data-list__item-content">
                                                <div class="pf-c-data-list__cell">
                                                    ${device.name || "-"}
                                                </div>
                                                <div class="pf-c-data-list__cell">
                                                    ${t`Created ${device.createdOn?.toLocaleString()}`}
                                                </div>
                                                <div class="pf-c-data-list__cell">
                                                    ${this.renderUpdate(device)}
                                                    ${this.renderDelete(device)}
                                                </div>
                                            </div>
                                        </div>
                                    </li>`;
                                });
                            }),
                    )}
                </ul>
            </div>
            <div class="pf-c-card__footer">
                ${this.configureUrl
                    ? html`<a
                          href="${this.configureUrl}?next=/%23%2Fuser"
                          class="pf-c-button pf-m-primary"
                          >${t`Configure WebAuthn`}
                      </a>`
                    : html``}
            </div>
        </div>`;
    }
}
