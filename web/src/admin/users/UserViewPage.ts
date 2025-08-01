import "#admin/groups/RelatedGroupList";
import "#admin/providers/rac/ConnectionTokenList";
import "#admin/rbac/ObjectPermissionsPage";
import "#admin/users/UserActiveForm";
import "#admin/users/UserApplicationTable";
import "#admin/users/UserChart";
import "#admin/users/UserForm";
import "#admin/users/UserImpersonateForm";
import "#admin/users/UserPasswordForm";
import "#components/DescriptionList";
import "#components/ak-page-header";
import "#components/ak-status-label";
import "#components/events/ObjectChangelog";
import "#components/events/UserEvents";
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

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { PFSize } from "#common/enums";
import { userTypeToLabel } from "#common/labels";
import { formatElapsedTime } from "#common/temporal";
import { me } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";

import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { renderRecoveryEmailRequest, requestRecoveryLink } from "#admin/users/UserListPage";

import {
    CapabilitiesEnum,
    CoreApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    SessionUser,
    User,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

@customElement("ak-user-view")
export class UserViewPage extends WithCapabilitiesConfig(AKElement) {
    @property({ type: Number })
    set userId(id: number) {
        me().then((me) => {
            this.me = me;
            new CoreApi(DEFAULT_CONFIG)
                .coreUsersRetrieve({
                    id: id,
                })
                .then((user) => {
                    this.user = user;
                });
        });
    }

    @property({ attribute: false })
    user?: User;

    @state()
    me?: SessionUser;

    static styles = [
        PFBase,
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
                max-width: 12rem;
            }
            .ak-button-collection > * {
                flex: 1 0 100%;
            }
            #reset-password-button {
                margin-right: 0;
            }

            #ak-email-recovery-request,
            #update-password-request .pf-c-button,
            #ak-email-recovery-request .pf-c-button {
                margin: 0;
                width: 100%;
            }
        `,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.user?.pk) return;
            this.userId = this.user?.pk;
        });
    }

    render() {
        return html`<ak-page-header
                icon="pf-icon pf-icon-user"
                header=${msg(str`User ${this.user?.username || ""}`)}
                description=${this.user?.name || ""}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderUserCard() {
        if (!this.user) {
            return nothing;
        }

        const user = this.user;

        // prettier-ignore
        const userInfo: DescriptionPair[] = [
            [msg("Username"), user.username],
            [msg("Name"), user.name],
            [msg("Email"), user.email || "-"],
            [msg("Last login"), user.lastLogin
                ? html`<div>${formatElapsedTime(user.lastLogin)}</div>
                      <small>${user.lastLogin.toLocaleString()}</small>`
                : html`${msg("-")}`],
            [msg("Last password change"), user.passwordChangeDate
                ? html`<div>${formatElapsedTime(user.passwordChangeDate)}</div>
                      <small>${user.passwordChangeDate.toLocaleString()}</small>`
                : html`${msg("-")}`],
            [msg("Active"), html`<ak-status-label type="warning" ?good=${user.isActive}></ak-status-label>`],
            [msg("Type"), userTypeToLabel(user.type)],
            [msg("Superuser"), html`<ak-status-label type="warning" ?good=${user.isSuperuser}></ak-status-label>`],
            [msg("Actions"), this.renderActionButtons(user)],
            [msg("Recovery"), this.renderRecoveryButtons(user)],
        ];

        return html`
            <div class="pf-c-card__title">${msg("User Info")}</div>
            <div class="pf-c-card__body">
                ${renderDescriptionList(userInfo, { twocolumn: true })}
            </div>
        `;
    }

    renderActionButtons(user: User) {
        const canImpersonate =
            this.can(CapabilitiesEnum.CanImpersonate) && user.pk !== this.me?.user.pk;

        return html`<div class="ak-button-collection">
            <ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update User")} </span>
                <ak-user-form slot="form" .instancePk=${user.pk}> </ak-user-form>
                <button slot="trigger" class="pf-m-primary pf-c-button pf-m-block">
                    ${msg("Edit")}
                </button>
            </ak-forms-modal>
            <ak-user-active-form
                .obj=${user}
                objectLabel=${msg("User")}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                        id: user.pk,
                        patchedUserRequest: {
                            isActive: !user.isActive,
                        },
                    });
                }}
            >
                <button slot="trigger" class="pf-c-button pf-m-warning pf-m-block">
                    <pf-tooltip
                        position="top"
                        content=${user.isActive
                            ? msg("Lock the user out of this system")
                            : msg("Allow the user to log in and use this system")}
                    >
                        ${user.isActive ? msg("Deactivate") : msg("Activate")}
                    </pf-tooltip>
                </button>
            </ak-user-active-form>
            ${canImpersonate
                ? html`
                      <ak-forms-modal size=${PFSize.Medium} id="impersonate-request">
                          <span slot="submit">${msg("Impersonate")}</span>
                          <span slot="header">${msg("Impersonate")} ${user.username}</span>
                          <ak-user-impersonate-form
                              slot="form"
                              .instancePk=${user.pk}
                          ></ak-user-impersonate-form>
                          <button slot="trigger" class="pf-c-button pf-m-secondary pf-m-block">
                              <pf-tooltip
                                  position="top"
                                  content=${msg("Temporarily assume the identity of this user")}
                              >
                                  <span>${msg("Impersonate")}</span>
                              </pf-tooltip>
                          </button>
                      </ak-forms-modal>
                  `
                : nothing}
        </div> `;
    }

    renderRecoveryButtons(user: User) {
        return html`<div class="ak-button-collection">
            <ak-forms-modal size=${PFSize.Medium} id="update-password-request">
                <span slot="submit">${msg("Update password")}</span>
                <span slot="header">
                    ${msg(str`Update ${user.name || user.username}'s password`)}
                </span>

                <ak-user-password-form
                    username=${user.username}
                    email=${ifDefined(user.email)}
                    slot="form"
                    .instancePk=${user.pk}
                >
                </ak-user-password-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary pf-m-block">
                    <pf-tooltip position="top" content=${msg("Enter a new password for this user")}>
                        ${msg("Set password")}
                    </pf-tooltip>
                </button>
            </ak-forms-modal>
            <ak-action-button
                id="reset-password-button"
                class="pf-m-secondary pf-m-block"
                .apiRequest=${() => requestRecoveryLink(user)}
            >
                <pf-tooltip
                    position="top"
                    content=${msg("Create a link for this user to reset their password")}
                >
                    ${msg("Create Recovery Link")}
                </pf-tooltip>
            </ak-action-button>
            ${user.email ? renderRecoveryEmailRequest(user) : nothing}
        </div> `;
    }

    renderTabCredentialsToken(user: User): TemplateResult {
        return html`
            <ak-tabs pageIdentifier="userCredentialsTokens" vertical>
                <section
                    slot="page-sessions"
                    data-tab-title="${msg("Sessions")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-session-list targetUser=${user.username}>
                            </ak-user-session-list>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-reputation"
                    data-tab-title="${msg("Reputation scores")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-reputation-list
                                targetUsername=${user.username}
                                targetEmail=${ifDefined(user.email)}
                            >
                            </ak-user-reputation-list>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-consent"
                    data-tab-title="${msg("Explicit Consent")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-consent-list userId=${user.pk}> </ak-user-consent-list>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-oauth-access"
                    data-tab-title="${msg("OAuth Access Tokens")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-access-token-list userId=${user.pk}>
                            </ak-user-oauth-access-token-list>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-oauth-refresh"
                    data-tab-title="${msg("OAuth Refresh Tokens")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-refresh-token-list userId=${user.pk}>
                            </ak-user-oauth-refresh-token-list>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-mfa-authenticators"
                    data-tab-title="${msg("MFA Authenticators")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-device-table userId=${user.pk}> </ak-user-device-table>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-source-connections"
                    data-tab-title="${msg("Connected services")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-user-settings-source userId=${user.pk} .canConnect=${false}>
                        </ak-user-settings-source>
                    </div>
                </section>
                <section
                    slot="page-rac-connection-tokens"
                    data-tab-title="${msg("RAC Connections")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-rac-connection-token-list userId=${user.pk}>
                        </ak-rac-connection-token-list>
                    </div>
                </section>
            </ak-tabs>
        `;
    }

    renderTabApplications(user: User): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__body">
                <ak-user-application-table .user=${user}></ak-user-application-table>
            </div>
        </div>`;
    }

    renderBody() {
        if (!this.user) {
            return nothing;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
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
                            ${Object.hasOwn(this.user?.attributes || {}, "notes")
                                ? html`${this.user.attributes?.notes}`
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
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.user.pk}
                                targetModelApp="authentik_core"
                                targetModelName="user"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </section>
            <section
                slot="page-groups"
                data-tab-title="${msg("Groups")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-group-related-list .targetUser=${this.user}> </ak-group-related-list>
                    </div>
                </div>
            </section>
            <section
                slot="page-events"
                data-tab-title="${msg("User events")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-events-user targetUser=${this.user.username}> </ak-events-user>
                    </div>
                </div>
            </section>
            <section slot="page-credentials" data-tab-title="${msg("Credentials / Tokens")}">
                ${this.renderTabCredentialsToken(this.user)}
            </section>
            <section
                slot="page-applications"
                data-tab-title="${msg("Applications")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                ${this.renderTabApplications(this.user)}
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikCoreUser}
                objectPk=${this.user.pk}
            >
            </ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-view": UserViewPage;
    }
}
