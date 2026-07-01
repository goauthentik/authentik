import "#admin/providers/rac/ConnectionTokenList";
import "#admin/users/UserTokenList";
import "#admin/users/oauth/UserAccessTokenList";
import "#admin/users/oauth/UserRefreshTokenList";
import "#elements/Tabs";
import "#elements/user/SessionList";
import "#elements/user/UserConsentList";
import "#elements/user/UserReputationList";
import "#elements/user/sources/SourceSettings";
import "./UserDevicesTable.js";

import { AKElement } from "#elements/Base";

import { User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-user-credentials-tab")
export class UserCredentialsTab extends AKElement {
    @property({ attribute: false })
    public user?: User;

    static styles = [PFPage, PFCard];

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        return html`<ak-tabs pageIdentifier="userCredentialsTokens" vertical>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-sessions"
                id="page-sessions"
                aria-label=${msg("Sessions")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-session-list targetUser=${this.user.username}></ak-user-session-list>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-tokens"
                id="page-tokens"
                aria-label=${msg("Tokens")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-admin-user-token-list .user=${this.user}></ak-admin-user-token-list>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-reputation"
                id="page-reputation"
                aria-label=${msg("Reputation scores")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-reputation-list
                        targetUsername=${this.user.username}
                        targetEmail=${ifDefined(this.user.email)}
                    ></ak-user-reputation-list>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-consent"
                id="page-consent"
                aria-label=${msg("Explicit Consent")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-consent-list userId=${this.user.pk}></ak-user-consent-list>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-oauth-access"
                id="page-oauth-access"
                aria-label=${msg("OAuth Access Tokens")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-oauth-access-token-list
                        userId=${this.user.pk}
                    ></ak-user-oauth-access-token-list>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-oauth-refresh"
                id="page-oauth-refresh"
                aria-label=${msg("OAuth Refresh Tokens")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-oauth-refresh-token-list
                        userId=${this.user.pk}
                    ></ak-user-oauth-refresh-token-list>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-mfa-authenticators"
                id="page-mfa-authenticators"
                aria-label=${msg("MFA Authenticators")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-device-table userId=${this.user.pk}></ak-user-device-table>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-source-connections"
                id="page-source-connections"
                aria-label=${msg("Connected services")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-user-settings-source user-id=${this.user.pk}></ak-user-settings-source>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-rac-connection-tokens"
                id="page-rac-connection-tokens"
                aria-label=${msg("RAC Connections")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-rac-connection-token-list
                        userId=${this.user.pk}
                    ></ak-rac-connection-token-list>
                </div>
            </div>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-credentials-tab": UserCredentialsTab;
    }
}
