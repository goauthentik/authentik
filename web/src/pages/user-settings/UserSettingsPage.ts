import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import { SourcesApi, StagesApi, UserSetting } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/Tabs";
import "../../elements/PageHeader";
import "./tokens/UserTokenList";
import "./UserSelfForm";
import "./settings/UserSettingsAuthenticatorDuo";
import "./settings/UserSettingsAuthenticatorStatic";
import "./settings/UserSettingsAuthenticatorTOTP";
import "./settings/UserSettingsAuthenticatorWebAuthn";
import "./settings/UserSettingsPassword";
import "./settings/SourceSettingsOAuth";
import { EVENT_REFRESH } from "../../constants";

@customElement("ak-user-settings")
export class UserSettingsPage extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFFlex,
            PFDisplay,
            PFGallery,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFSizing,
            PFForm,
            PFFormControl,
            AKGlobal,
        ];
    }

    @property({ attribute: false })
    userSettings?: Promise<UserSetting[]>;

    @property({ attribute: false })
    sourceSettings?: Promise<UserSetting[]>;

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.firstUpdated();
        });
    }

    firstUpdated(): void {
        this.userSettings = new StagesApi(DEFAULT_CONFIG).stagesAllUserSettingsList();
        this.sourceSettings = new SourcesApi(DEFAULT_CONFIG).sourcesAllUserSettingsList();
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

    renderSourceSettings(source: UserSetting): TemplateResult {
        switch (source.component) {
            case "ak-user-settings-source-oauth":
                return html`<ak-user-settings-source-oauth
                    objectId=${source.objectUid}
                    title=${source.title}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-oauth>`;
            default:
                return html`<p>${t`Error: unsupported source settings: ${source.component}`}</p>`;
        }
    }

    render(): TemplateResult {
        return html`<div class="pf-c-page">
            <main role="main" class="pf-c-page__main" tabindex="-1">
                <ak-page-header
                    icon="pf-icon pf-icon-user"
                    header=${t`User Settings`}
                    description=${t`Configure settings relevant to your user profile.`}
                >
                </ak-page-header>
                <ak-tabs ?vertical="${true}" style="height: 100%;">
                    <section
                        slot="page-details"
                        data-tab-title="${t`User details`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-c-card">
                            <div class="pf-c-card__title">${t`Update details`}</div>
                            <div class="pf-c-card__body">
                                <ak-user-self-form .instancePk=${1}></ak-user-self-form>
                            </div>
                        </div>
                    </section>
                    <section
                        slot="page-tokens"
                        data-tab-title="${t`Tokens`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-user-token-list></ak-user-token-list>
                    </section>
                    ${until(
                        this.userSettings?.then((stages) => {
                            return stages.map((stage) => {
                                return html`<section
                                    slot="page-${stage.objectUid}"
                                    data-tab-title="${ifDefined(stage.title)}"
                                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                                >
                                    ${this.renderStageSettings(stage)}
                                </section>`;
                            });
                        }),
                    )}
                    ${until(
                        this.sourceSettings?.then((source) => {
                            return source.map((stage) => {
                                return html`<section
                                    slot="page-${stage.objectUid}"
                                    data-tab-title="${ifDefined(stage.title)}"
                                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                                >
                                    ${this.renderSourceSettings(stage)}
                                </section>`;
                            });
                        }),
                    )}
                </ak-tabs>
            </main>
        </div>`;
    }
}
