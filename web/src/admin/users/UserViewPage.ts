import "#admin/groups/RelatedGroupList";
import "#admin/roles/ak-related-role-table";
import "#admin/providers/rac/ConnectionTokenList";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/users/UserActiveForm";
import "#admin/users/UserApplicationTable";
import "#admin/users/UserChart";
import "#admin/users/UserForm";
import "#admin/users/UserImpersonateForm";
import "#admin/users/UserPasswordForm";
import "#components/DescriptionList";
import "#components/ak-object-attributes-card";
import "#components/ak-status-label";
import "#admin/events/ObjectChangelog";
import "#admin/events/UserEvents";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/ModalForm";
import "#elements/oauth/UserAccessTokenList";
import "#elements/oauth/UserRefreshTokenList";
import "#elements/user/SessionList";
import "#elements/user/UserConsentList";
import "#elements/user/UserReputationList";
import "#elements/user/sources/SourceSettings";
import "./UserDevicesTable.js";
import "#elements/ak-mdx/ak-mdx";

import { DEFAULT_CONFIG } from "#common/api/config";
import { AKRefreshEvent } from "#common/events";
import { userTypeToLabel } from "#common/labels";
import { formatDisambiguatedUserDisplayName, formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithLocale } from "#elements/mixins/locale";
import { WithSession } from "#elements/mixins/session";
import { Timestamp } from "#elements/table/shared";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";
import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { RecoveryButtons } from "#admin/users/recovery";
import { ToggleUserActivationButton } from "#admin/users/UserActiveForm";
import { UserForm } from "#admin/users/UserForm";
import { UserImpersonateForm } from "#admin/users/UserImpersonateForm";

import { CapabilitiesEnum, CoreApi, ModelEnum, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

@customElement("ak-user-view")
export class UserViewPage extends WithLicenseSummary(
    WithLocale(WithBrandConfig(WithCapabilitiesConfig(WithSession(AKElement)))),
) {
    #api = new CoreApi(DEFAULT_CONFIG);

    @property({ type: Number, useDefault: true })
    public userId: number | null = null;

    @property({ attribute: false, useDefault: true })
    public user: User | null = null;

    static styles = [
        PFPage,
        PFButton,
        PFDisplay,
        PFGrid,
        PFContent,
        PFCard,
        PFDescriptionList,
        PFSizing,
        PFBanner,
        css`
            .ak-button-collection {
                display: flex;
                flex-direction: column;
                gap: 0.375rem;
                max-width: 13rem;
            }
            .ak-button-collection > * {
                flex: 1 0 100%;
            }
            #reset-password-button {
                margin-right: 0;
            }
        `,
    ];

    @listen(AKRefreshEvent)
    public refresh = () => {
        if (!this.userId) {
            return;
        }

        return this.#api
            .coreUsersRetrieve({
                id: this.userId!,
            })
            .then((user) => {
                this.user = user;
            })
            .catch(showAPIErrorMessage);
    };

    protected override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (changed.has("userId") && this.userId !== null) {
            this.refresh();
        }

        if (changed.has("user") && this.user) {
            const { username, avatar, name, email } = this.user;
            const icon = avatar ?? "pf-icon pf-icon-user";

            setPageDetails({
                icon,
                iconImage: !!avatar,
                header: username ? msg(str`User ${username}`) : msg("User"),
                description: this.user
                    ? formatDisambiguatedUserDisplayName({ name, email }, this.activeLanguageTag)
                    : null,
            });
        }
    }

    protected renderUserCard() {
        if (!this.user) {
            return null;
        }

        const user = this.user;

        // prettier-ignore
        const userInfo: DescriptionPair[] = [
            [ msg("Username"), user.username ],
            [ msg("Name"), user.name ],
            [ msg("Email"), user.email || "-" ],
            [ msg("Last login"), Timestamp(user.lastLogin) ],
            [ msg("Last password change"), Timestamp(user.passwordChangeDate) ],
            [ msg("Active"), html`<ak-status-label ?good=${user.isActive}></ak-status-label>` ],
            [ msg("Type"), userTypeToLabel(user.type) ],
            [ msg("Superuser"), html`<ak-status-label type="warning" ?good=${user.isSuperuser}></ak-status-label>` ],
            [ msg("Actions"), this.renderActionButtons(user) ],
            [ msg("Recovery"), this.renderRecoveryButtons(user) ],
        ]

        return html`
            <div class="pf-c-card__title">${msg("User Info")}</div>
            <div class="pf-c-card__body">
                ${renderDescriptionList(userInfo, { twocolumn: true })}
            </div>
        `;
    }

    protected renderActionButtons(user: User): SlottedTemplateResult {
        const showImpersonate =
            this.can(CapabilitiesEnum.CanImpersonate) && user.pk !== this.currentUser?.pk;

        const displayName = formatUserDisplayName(user);

        return html`<div class="ak-button-collection">
            <button
                class="pf-m-primary pf-c-button pf-m-block"
                ${UserForm.asInstanceInvoker(user.pk)}
            >
                ${msg("Edit User")}
            </button>

            ${ToggleUserActivationButton(user, { className: "pf-m-block" })}
            ${showImpersonate
                ? html`<button
                      class="pf-c-button pf-m-tertiary pf-m-block"
                      ${UserImpersonateForm.asInstanceInvoker(user.pk)}
                      aria-label=${msg(str`Impersonate ${displayName}`)}
                  >
                      <pf-tooltip
                          position="top"
                          content=${msg("Temporarily assume the identity of this user")}
                      >
                          <span>${msg("Impersonate")}</span>
                      </pf-tooltip>
                  </button>`
                : null}
        </div> `;
    }

    protected renderRecoveryButtons(user: User) {
        return html`<div class="ak-button-collection">
            ${RecoveryButtons({
                user,
                brandHasRecoveryFlow: !!this.brand.flowRecovery,
                buttonClasses: "pf-m-block",
            })}
        </div>`;
    }

    protected renderTabCredentialsToken(user: User): TemplateResult {
        return html`
            <ak-tabs pageIdentifier="userCredentialsTokens" vertical>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-sessions"
                    id="page-sessions"
                    aria-label=${msg("Sessions")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                            <ak-user-session-list targetUser=${user.username}>
                            </ak-user-session-list>
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
                                targetUsername=${user.username}
                                targetEmail=${ifDefined(user.email)}
                            >
                            </ak-user-reputation-list>
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
                            <ak-user-consent-list userId=${user.pk}> </ak-user-consent-list>
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
                            <ak-user-oauth-access-token-list userId=${user.pk}>
                            </ak-user-oauth-access-token-list>
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
                            <ak-user-oauth-refresh-token-list userId=${user.pk}>
                            </ak-user-oauth-refresh-token-list>
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
                            <ak-user-device-table userId=${user.pk}> </ak-user-device-table>
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
                        <ak-user-settings-source user-id=${user.pk}>
                        </ak-user-settings-source>
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
                        <ak-rac-connection-token-list userId=${user.pk}>
                        </ak-rac-connection-token-list>
                    </div>
                </div>
            </ak-tabs>
</main>
        `;
    }

    protected renderTabApplications(user: User): TemplateResult {
        return html`<div class="pf-c-card">
            <ak-user-application-table .user=${user}></ak-user-application-table>
        </div>`;
    }

    protected renderTabRoles(user: User): TemplateResult {
        return html`
            <ak-tabs pageIdentifier="userRoles" vertical>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-assigned-roles"
                    id="page-assigned-roles"
                    aria-label=${msg("Assigned Roles")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-related-role-table .targetUser=${user}></ak-related-role-table>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-all-roles"
                    id="page-all-roles"
                    aria-label=${msg("All Roles")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-related-role-table
                            .targetUser=${user}
                            showInherited
                        ></ak-related-role-table>
                    </div>
                </div>
            </ak-tabs>
        `;
    }

    protected override render() {
        if (!this.user) {
            return null;
        }

        return html`<main>
            <ak-tabs>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label=${msg("Overview")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-5-col-on-xl pf-m-5-col-on-2xl"
                        >
                            ${this.renderUserCard()}
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-7-col-on-xl pf-m-7-col-on-2xl"
                        >
                            <div class="pf-c-card__title">
                                ${msg("Actions over the last week (per 8 hours)")}
                            </div>
                            <div class="pf-c-card__body">
                                <ak-charts-user username=${this.user.username}> </ak-charts-user>
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Notes")}</div>
                            <div class="pf-c-card__body">
                                ${this.user?.attributes?.notes
                                    ? html`<ak-mdx .content=${this.user.attributes.notes}></ak-mdx>`
                                    : html`
                                          <p>
                                              ${msg(
                                                  "Edit the notes attribute of this user to add notes here.",
                                              )}
                                          </p>
                                      `}
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Changelog")}</div>
                            <ak-object-changelog
                                targetModelPk=${this.user.pk}
                                targetModelName=${ModelEnum.AuthentikCoreUser}
                            >
                            </ak-object-changelog>
                        </div>
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <ak-object-attributes-card
                                .objectAttributes=${this.user.attributes}
                            ></ak-object-attributes-card>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-groups"
                    id="page-groups"
                    aria-label=${msg("Groups")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-group-related-list .targetUser=${this.user}> </ak-group-related-list>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-roles"
                    id="page-roles"
                    aria-label=${msg("Roles")}
                >
                    ${this.renderTabRoles(this.user)}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-events"
                    id="page-events"
                    aria-label=${msg("User events")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-events-user targetUser=${this.user.username}> </ak-events-user>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-credentials"
                    id="page-credentials"
                    aria-label=${msg("Credentials / Tokens")}
                >
                    ${this.renderTabCredentialsToken(this.user)}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-applications"
                    id="page-applications"
                    aria-label=${msg("Applications")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    ${this.renderTabApplications(this.user)}
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label=${msg("Permissions")}
                    model=${ModelEnum.AuthentikCoreUser}
                    objectPk=${this.user.pk}
                >
                </ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-view": UserViewPage;
    }
}
