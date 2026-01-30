import "#elements/Tabs";
import "#elements/forms/ModalForm";
import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/user/SessionList";
import "#elements/user/UserConsentList";
import "#elements/user/sources/SourceSettings";
import "#user/user-settings/details/UserPassword";
import "#user/user-settings/details/UserSettingsFlowExecutor";
import "#user/user-settings/mfa/MFADevicesPage";
import "#user/user-settings/tokens/UserTokenList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKSkipToContent } from "#elements/a11y/ak-skip-to-content";
import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithSession } from "#elements/mixins/session";
import { ifPresent } from "#elements/utils/attributes";

import Styles from "#user/user-settings/styles.css";

import { CoreApi, StagesApi, UserSetting } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

@customElement("ak-user-settings")
export class UserSettingsPage extends WithLicenseSummary(WithSession(AKElement)) {
    static styles: CSSResult[] = [
        PFPage,
        PFButton,
        PFDisplay,
        PFGallery,
        PFContent,
        PFCard,
        PFDescriptionList,
        PFSizing,
        PFForm,
        PFFormControl,
        PFStack,
        Styles,
    ];

    @state()
    userSettings?: UserSetting[];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.firstUpdated();
        });
    }

    async firstUpdated(): Promise<void> {
        this.userSettings = await new StagesApi(DEFAULT_CONFIG).stagesAllUserSettingsList();
    }

    render(): TemplateResult {
        const pwStage =
            this.userSettings?.filter((stage) => stage.component === "ak-user-settings-password") ||
            [];

        const { currentUser } = this;

        return html`<div class="pf-c-page">
            <div class="pf-c-page__main">
                <ak-tabs
                    vertical
                    role="main"
                    aria-label=${msg("User settings")}
                    ${AKSkipToContent.ref}
                >
                    <div
                        id="page-details"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-details"
                        aria-label=${msg("User details")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-l-stack pf-m-gutter">
                            <div class="pf-l-stack__item">
                                <ak-user-settings-flow-executor></ak-user-settings-flow-executor>
                            </div>
                            <div class="pf-l-stack__item">
                                ${pwStage.length > 0
                                    ? html`<ak-user-settings-password
                                          configureUrl=${ifDefined(pwStage[0].configureUrl)}
                                      ></ak-user-settings-password>`
                                    : nothing}
                            </div>
                        </div>
                    </div>
                    <div
                        id="page-sessions"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-sessions"
                        aria-label=${msg("Sessions")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-c-card">
                            <div class="pf-c-card__body">
                                <ak-user-session-list
                                    targetUser=${ifPresent(currentUser?.username)}
                                ></ak-user-session-list>
                            </div>
                        </div>
                    </div>
                    <div
                        id="page-consents"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-consents"
                        aria-label=${msg("Consent")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-c-card">
                            <div class="pf-c-card__body">
                                <ak-user-consent-list
                                    userId=${ifPresent(currentUser?.pk)}
                                ></ak-user-consent-list>
                            </div>
                        </div>
                    </div>
                    <div
                        id="page-mfa"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-mfa"
                        aria-label=${msg("MFA Devices")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-c-card">
                            <div class="pf-c-card__body">
                                <ak-user-settings-mfa
                                    .userSettings=${this.userSettings}
                                ></ak-user-settings-mfa>
                            </div>
                        </div>
                    </div>
                    <div
                        id="page-sources"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-sources"
                        aria-label=${msg("Connected services")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-c-card">
                            <div class="pf-c-card__title">
                                ${msg(
                                    "Connect your user account to the services listed below, to allow you to login using the service instead of traditional credentials.",
                                )}
                            </div>
                            <ak-user-settings-source
                                allow-configuration
                                user-id=${ifPresent(currentUser?.pk)}
                            ></ak-user-settings-source>
                        </div>
                    </div>
                    <div
                        id="page-tokens"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-tokens"
                        aria-label=${msg("Tokens and App passwords")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <div class="pf-c-card">
                            <div class="pf-c-card__body">
                                <ak-user-token-list></ak-user-token-list>
                            </div>
                        </div>
                    </div>
                    ${this.hasEnterpriseLicense
                        ? html`
                              <div
                                  id="page-security"
                                  role="tabpanel"
                                  tabindex="0"
                                  slot="page-security"
                                  aria-label=${msg("Security")}
                                  class="pf-c-page__main-section pf-m-no-padding-mobile"
                              >
                                  <div class="pf-l-stack pf-m-gutter">
                                      <div class="pf-l-stack__item">
                                          <div class="pf-c-card">
                                              <div class="pf-c-card__title">
                                                  ${msg(
                                                      "If you suspect your account has been compromised, you can immediately lock it down. This will sign you out of all sessions, invalidate your password, and revoke all tokens.",
                                                  )}
                                              </div>
                                              <div class="pf-c-card__body">
                                                  <button
                                                      class="pf-c-button pf-m-danger"
                                                      @click=${async () => {
                                                          const response = await new CoreApi(
                                                              DEFAULT_CONFIG,
                                                          ).coreUsersAccountLockdownCreate({
                                                              userAccountLockdownRequest: {},
                                                          });
                                                          if (response.flowUrl) {
                                                              window.location.assign(
                                                                  response.flowUrl,
                                                              );
                                                          }
                                                      }}
                                                  >
                                                      ${msg("Lock my account")}
                                                  </button>
                                              </div>
                                          </div>
                                      </div>
                                  </div>
                              </div>
                          `
                        : nothing}
                </ak-tabs>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings": UserSettingsPage;
    }
}
