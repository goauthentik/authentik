import { StagesApi, UserSetting } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { EVENT_REFRESH } from "../../../constants";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

import "../../../elements/EmptyState";
import "./UserSettingsAuthenticatorDuo";
import "./UserSettingsAuthenticatorStatic";
import "./UserSettingsAuthenticatorTOTP";
import "./UserSettingsAuthenticatorWebAuthn";
import "./UserSettingsPassword";

@customElement("ak-user-settings-stage")
export class UserStageSettingsPage extends LitElement {
    @property({ attribute: false })
    userSettings?: Promise<UserSetting[]>;

    static get styles(): CSSResult[] {
        return [PFStack];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.firstUpdated();
        });
    }

    firstUpdated(): void {
        this.userSettings = new StagesApi(DEFAULT_CONFIG).stagesAllUserSettingsList();
    }

    renderStageSettings(stage: UserSetting): TemplateResult {
        switch (stage.component) {
            case "ak-user-settings-authenticator-webauthn":
                return html`<ak-user-settings-authenticator-webauthn
                    objectId=${stage.objectUid}
                    .configureUrl=${stage.configureUrl}
                >
                </ak-user-settings-authenticator-webauthn>`;
            case "ak-user-settings-password":
                return html`<ak-user-settings-password
                    objectId=${stage.objectUid}
                    .configureUrl=${stage.configureUrl}
                >
                </ak-user-settings-password>`;
            case "ak-user-settings-authenticator-totp":
                return html`<ak-user-settings-authenticator-totp
                    objectId=${stage.objectUid}
                    .configureUrl=${stage.configureUrl}
                >
                </ak-user-settings-authenticator-totp>`;
            case "ak-user-settings-authenticator-static":
                return html`<ak-user-settings-authenticator-static
                    objectId=${stage.objectUid}
                    .configureUrl=${stage.configureUrl}
                >
                </ak-user-settings-authenticator-static>`;
            case "ak-user-settings-authenticator-duo":
                return html`<ak-user-settings-authenticator-duo
                    objectId=${stage.objectUid}
                    .configureUrl=${stage.configureUrl}
                >
                </ak-user-settings-authenticator-duo>`;
            default:
                return html`<p>${t`Error: unsupported stage settings: ${stage.component}`}</p>`;
        }
    }

    render(): TemplateResult {
        return html`<div class="pf-l-stack pf-m-gutter">
            ${until(
                this.userSettings?.then((stages) => {
                    return stages.map((stage) => {
                        return html`<div class="pf-l-stack__item">
                            ${this.renderStageSettings(stage)}
                        </div>`;
                    });
                }),
                html`<ak-empty-state ?loading="${true}" header=${t`Loading`}></ak-empty-state>`,
            )}
        </div>`;
    }
}
