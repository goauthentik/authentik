import { AuthenticatorsApi, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { FlowURLManager } from "../../../api/legacy";
import { BaseUserSettings } from "./BaseUserSettings";

@customElement("ak-user-settings-authenticator-static")
export class UserSettingsAuthenticatorStatic extends BaseUserSettings {

    renderEnabled(): TemplateResult {
        return html`<div class="pf-c-card__body">
                <p>
                    ${gettext("Status: Enabled")}
                    <i class="pf-icon pf-icon-ok"></i>
                </p>
            </div>
            <div class="pf-c-card__footer">
                <button
                    class="pf-c-button pf-m-danger"
                    @click=${() => {
                        return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsTotpList({}).then((devices) => {
                            if (devices.results.length < 1) {
                                return;
                            }
                            // TODO: Handle multiple devices, currently we assume only one TOTP Device
                            return new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsTotpDelete({
                                id: devices.results[0].pk || 0
                            });
                        });
                    }}>
                    ${gettext("Disable Time-based OTP")}
                </button>
            </div>`;
    }

    renderDisabled(): TemplateResult {
        return html`
            <div class="pf-c-card__body">
                <p>
                    ${gettext("Status: Disabled")}
                    <i class="pf-icon pf-icon-error-circle-o"></i>
                </p>
            </div>
            <div class="pf-c-card__footer">
                ${until(new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpRead({ stageUuid: this.objectId}).then((stage) => {
                    if (stage.configureFlow) {
                        return html`<a href="${FlowURLManager.configure(stage.pk || "", "?next=/%23%2Fuser")}"
                                class="pf-c-button pf-m-primary">${gettext("Enable Time-based OTP")}
                            </a>`;
                    }
                    return html``;
                }))}
            </div>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${gettext("Time-based One-Time Passwords")}
            </div>
            ${until(new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsTotpList({}).then((devices) => {
                return devices.results.length > 0 ? this.renderEnabled() : this.renderDisabled();
            }))}
        </div>`;
    }

}
