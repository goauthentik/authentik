import "@goauthentik/admin/groups/RelatedGroupList";
import "@goauthentik/admin/users/UserActiveForm";
import "@goauthentik/admin/users/UserChart";
import "@goauthentik/admin/users/UserForm";
import "@goauthentik/admin/users/UserPasswordForm";
import "@goauthentik/app/admin/users/UserAssignedGlobalPermissionsTable";
import "@goauthentik/app/admin/users/UserAssignedObjectPermissionsTable";
import {
    renderRecoveryEmailRequest,
    requestRecoveryLink,
} from "@goauthentik/app/admin/users/UserListPage";
import { me } from "@goauthentik/app/common/users";
import "@goauthentik/app/elements/rbac/ObjectPermissionsPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { userTypeToLabel } from "@goauthentik/common/labels";
import "@goauthentik/components/DescriptionList";
import {
    type DescriptionPair,
    renderDescriptionList,
} from "@goauthentik/components/DescriptionList";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/components/events/ObjectChangelog";
import "@goauthentik/components/events/UserEvents";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/PageHeader";
import { PFSize } from "@goauthentik/elements/Spinner";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/oauth/UserRefreshList";
import "@goauthentik/elements/user/SessionList";
import "@goauthentik/elements/user/UserConsentList";

import { msg, str } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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

import {
    CapabilitiesEnum,
    CoreApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    SessionUser,
    User,
} from "@goauthentik/api";

import "./UserDevicesTable";

@customElement("ak-user-view")
export class UserViewPage extends AKElement {
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

    static get styles() {
        return [
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
    }

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
            [msg("Last login"), user.lastLogin?.toLocaleString()],
            [msg("Active"), html`<ak-status-label type="warning" ?good=${user.isActive}></ak-status-label>`],
            [msg("Type"), userTypeToLabel(user.type)],
            [msg("Superuser"), html`<ak-status-label type="warning" ?good=${user.isSuperuser}></ak-status-label>`],
            [msg("Actions"), this.renderActionButtons(user)],
            [msg("Recovery"), this.renderRecoveryButtons(user)],
        ];

        return html`
            <div class="pf-c-card__title">${msg("User Info")}</div>
            <div class="pf-c-card__body">${renderDescriptionList(userInfo)}</div>
        `;
    }

    renderActionButtons(user: User) {
        const canImpersonate =
            rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanImpersonate) &&
            user.pk !== this.me?.user.pk;

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
                      <ak-action-button
                          class="pf-m-secondary pf-m-block"
                          id="impersonate-user-button"
                          .apiRequest=${() => {
                              return new CoreApi(DEFAULT_CONFIG)
                                  .coreUsersImpersonateCreate({
                                      id: user.pk,
                                  })
                                  .then(() => {
                                      window.location.href = "/";
                                  });
                          }}
                      >
                          <pf-tooltip
                              position="top"
                              content=${msg("Temporarily assume the identity of this user")}
                          >
                              ${msg("Impersonate")}
                          </pf-tooltip>
                      </ak-action-button>
                  `
                : nothing}
        </div> `;
    }

    renderRecoveryButtons(user: User) {
        return html`<div class="ak-button-collection">
                                <ak-forms-modal size=${PFSize.Medium} id="update-password-request">
                                    <span slot="submit">${msg("Update password")}</span>
                                    <span slot="header">${msg("Update password")}</span>
                                    <ak-user-password-form
                                        slot="form"
                                        .instancePk=${user.pk}
                                    ></ak-user-password-form>
                                    <button
                                        slot="trigger"
                                        class="pf-c-button pf-m-secondary pf-m-block"
                                    >
                                        <pf-tooltip
                                            position="top"
                                            content=${msg("Enter a new password for this user")}
                                        >
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
                                        content=${msg(
                                            "Create a link for this user to reset their password",
                                        )}
                                    >
                                        ${msg("Create Recovery Link")}
                                    </pf-tooltip>
                                </ak-action-button>
                                ${user.email ? renderRecoveryEmailRequest(user) : nothing}
                            </div>
                        </dd>
                    </div>
                </dl>
            </div>
        `;
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
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                    >
                        ${this.renderUserCard()}
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                    >
                        <div class="pf-c-card__title">
                            ${msg("Actions over the last week (per 8 hours)")}
                        </div>
                        <div class="pf-c-card__body">
                            <ak-charts-user userId=${this.user.pk || 0}> </ak-charts-user>
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
                slot="page-sessions"
                data-tab-title="${msg("Sessions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-user-session-list targetUser=${this.user.username}>
                        </ak-user-session-list>
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
            <section
                slot="page-consent"
                data-tab-title="${msg("Explicit Consent")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-user-consent-list userId=${this.user.pk}> </ak-user-consent-list>
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
                        <ak-user-oauth-refresh-list userId=${this.user.pk}>
                        </ak-user-oauth-refresh-list>
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
                        <ak-user-device-table userId=${this.user.pk}> </ak-user-device-table>
                    </div>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.CoreUser}
                objectPk=${this.user.pk}
            ></ak-rbac-object-permission-page>
            <div
                slot="page-mfa-assigned-permissions"
                data-tab-title="${msg("Assigned permissions")}"
                class=""
            >
                <div class="pf-c-banner pf-m-info">
                    ${msg("RBAC is in preview.")}
                    <a href="mailto:hello+feature/rbac@goauthentik.io"
                        >${msg("Send us feedback!")}</a
                    >
                </div>
                <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__title">
                                ${msg("Assigned global permissions")}
                            </div>
                            <div class="pf-c-card__body">
                                <ak-user-assigned-global-permissions-table userId=${this.user.pk}>
                                </ak-user-assigned-global-permissions-table>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__title">
                                ${msg("Assigned object permissions")}
                            </div>
                            <div class="pf-c-card__body">
                                <ak-user-assigned-object-permissions-table userId=${this.user.pk}>
                                </ak-user-assigned-object-permissions-table>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </ak-tabs>`;
    }
}
