import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/user/SessionList";
import "@goauthentik/elements/user/UserConsentList";
import "@goauthentik/user/user-settings/details/UserPassword";
import "@goauthentik/user/user-settings/details/UserSettingsFlowExecutor";
import "@goauthentik/user/user-settings/mfa/MFADevicesPage";
import "@goauthentik/user/user-settings/sources/SourceSettings";
import "@goauthentik/user/user-settings/tokens/UserTokenList";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

import { StagesApi, UserSetting } from "@goauthentik/api";

@customElement("ak-user-settings")
export class UserSettingsPage extends AKElement {
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
            PFStack,
            AKGlobal,
            css`
                @media screen and (min-width: 1200px) {
                    :host {
                        width: 90rem;
                        margin-left: auto;
                        margin-right: auto;
                    }
                }
            `,
        ];
    }

    @state()
    userSettings!: Promise<UserSetting[]>;

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.firstUpdated();
        });
    }

    firstUpdated(): void {
        this.userSettings = new StagesApi(DEFAULT_CONFIG).stagesAllUserSettingsList();
    }

    render(): TemplateResult {
        return html`<div class="pf-c-page">
            <main role="main" class="pf-c-page__main" tabindex="-1">
                <ak-tabs ?vertical="${true}">
                    <section
                        slot="page-details"
                        data-tab-title="${t`User details`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-l-stack pf-m-gutter">
                            <div class="pf-l-stack__item">
                                <ak-user-settings-flow-executor></ak-user-settings-flow-executor>
                            </div>
                            <div class="pf-l-stack__item">
                                ${until(
                                    this.userSettings?.then((settings) => {
                                        const pwStage = settings.filter(
                                            (stage) =>
                                                stage.component === "ak-user-settings-password",
                                        );
                                        if (pwStage.length > 0) {
                                            return html`<ak-user-settings-password
                                                configureUrl=${ifDefined(pwStage[0].configureUrl)}
                                            ></ak-user-settings-password>`;
                                        }
                                    }),
                                )}
                            </div>
                        </div>
                    </section>
                    <section
                        slot="page-sessions"
                        data-tab-title="${t`Sessions`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        ${until(
                            me().then((u) => {
                                return html`<ak-user-session-list
                                    targetUser=${u.user.username}
                                ></ak-user-session-list>`;
                            }),
                        )}
                    </section>
                    <section
                        slot="page-consents"
                        data-tab-title="${t`Consent`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        ${until(
                            me().then((u) => {
                                return html`<ak-user-consent-list
                                    userId=${u.user.pk}
                                ></ak-user-consent-list>`;
                            }),
                        )}
                    </section>
                    <section
                        slot="page-mfa"
                        data-tab-title="${t`MFA Devices`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-user-settings-mfa
                            .userSettings=${this.userSettings}
                        ></ak-user-settings-mfa>
                    </section>
                    <section
                        slot="page-sources"
                        data-tab-title="${t`Connected services`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-user-settings-source></ak-user-settings-source>
                    </section>
                    <section
                        slot="page-tokens"
                        data-tab-title="${t`Tokens and App passwords`}"
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-user-token-list></ak-user-token-list>
                    </section>
                </ak-tabs>
            </main>
        </div>`;
    }
}
