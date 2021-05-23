import { AuthenticatorsApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { FlowURLManager } from "../../../api/legacy";
import { BaseUserSettings } from "./BaseUserSettings";

@customElement("ak-user-settings-authenticator-duo")
export class UserSettingsAuthenticatorDuo extends BaseUserSettings {

    @property({ type: Boolean })
    configureFlow = false;

    renderEnabled(): TemplateResult {
        return html`<div class="pf-c-card__body">
                <p>
                    ${t`Status: Enabled`}
                    <i class="pf-icon pf-icon-ok"></i>
                </p>
                <ul class="ak-otp-tokens">
                    ${until(new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsStaticList({}).then((devices) => {
                        if (devices.results.length < 1) {
                            return;
                        }
                        return devices.results[0].tokenSet?.map((token) => {
                            return html`<li>${token.token}</li>`;
                        });
                    }))}
                </ul>
            </div>
            <div class="pf-c-card__footer">
                <button
                    class="pf-c-button pf-m-danger"
                    @click=${() => {
                        return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsStaticList({}).then((devices) => {
                            if (devices.results.length < 1) {
                                return;
                            }
                            // TODO: Handle multiple devices, currently we assume only one TOTP Device
                            return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsStaticDestroy({
                                id: devices.results[0].pk || 0
                            });
                        });
                    }}>
                    ${t`Disable Static Tokens`}
                </button>
            </div>`;
    }

    renderDisabled(): TemplateResult {
        return html`
            <div class="pf-c-card__body">
                <p>
                    ${t`Status: Disabled`}
                    <i class="pf-icon pf-icon-error-circle-o"></i>
                </p>
            </div>
            <div class="pf-c-card__footer">
                ${this.configureFlow ?
                    html`<a href="${FlowURLManager.configure(this.objectId || "", "?next=/%23%2Fuser")}"
                            class="pf-c-button pf-m-primary">${t`Enable Static Tokens`}
                        </a>`: html``}
            </div>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${t`Duo`}
            </div>
            ${this.renderDisabled()}
            ${until(new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsStaticList({}).then((devices) => {
                return devices.results.length > 0 ? this.renderEnabled() : this.renderDisabled();
            }))}
        </div>`;
    }

}
