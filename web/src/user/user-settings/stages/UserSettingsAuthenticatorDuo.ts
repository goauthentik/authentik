import { AuthenticatorsApi } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators";
import { until } from "lit/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { BaseUserSettings } from "../BaseUserSettings";
import { EVENT_REFRESH } from "../../../constants";

@customElement("ak-user-settings-authenticator-duo")
export class UserSettingsAuthenticatorDuo extends BaseUserSettings {
    renderEnabled(): TemplateResult {
        return html`<div class="pf-c-card__body">
                <p>
                    ${t`Status: Enabled`}
                    <i class="pf-icon pf-icon-ok"></i>
                </p>
            </div>
            <div class="pf-c-card__footer">
                <button
                    class="pf-c-button pf-m-danger"
                    @click=${() => {
                        return new AuthenticatorsApi(DEFAULT_CONFIG)
                            .authenticatorsDuoList({})
                            .then((devices) => {
                                if (devices.results.length < 1) {
                                    return;
                                }
                                // TODO: Handle multiple devices, currently we assume only one TOTP Device
                                return new AuthenticatorsApi(DEFAULT_CONFIG)
                                    .authenticatorsDuoDestroy({
                                        id: devices.results[0].pk || 0,
                                    })
                                    .then(() => {
                                        this.dispatchEvent(
                                            new CustomEvent(EVENT_REFRESH, {
                                                bubbles: true,
                                                composed: true,
                                            }),
                                        );
                                    });
                            });
                    }}
                >
                    ${t`Disable Duo authenticator`}
                </button>
            </div>`;
    }

    renderDisabled(): TemplateResult {
        return html` <div class="pf-c-card__body">
                <p>
                    ${t`Status: Disabled`}
                    <i class="pf-icon pf-icon-error-circle-o"></i>
                </p>
            </div>
            <div class="pf-c-card__footer">
                ${this.configureUrl
                    ? html`<a
                          href="${this.configureUrl}?next=/${encodeURIComponent("#/settings")}"
                          class="pf-c-button pf-m-primary"
                          >${t`Enable Duo authenticator`}
                      </a>`
                    : html``}
            </div>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${t`Duo`}</div>
            ${until(
                new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsDuoList({}).then((devices) => {
                    return devices.results.length > 0
                        ? this.renderEnabled()
                        : this.renderDisabled();
                }),
            )}
        </div>`;
    }
}
