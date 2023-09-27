import "@goauthentik/admin/groups/RelatedGroupList";
import "@goauthentik/admin/users/UserActiveForm";
import "@goauthentik/admin/users/UserChart";
import "@goauthentik/admin/users/UserForm";
import "@goauthentik/admin/users/UserPasswordForm";
import { me } from "@goauthentik/app/common/users";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import "@goauthentik/components/events/ObjectChangelog";
import "@goauthentik/components/events/UserEvents";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/PageHeader";
import { PFSize } from "@goauthentik/elements/Spinner";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/oauth/UserRefreshList";
import "@goauthentik/elements/user/SessionList";
import "@goauthentik/elements/user/UserConsentList";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

import { CapabilitiesEnum, CoreApi, SessionUser, User } from "@goauthentik/api";

import "./UserDevicesList";

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

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFFlex,
            PFButton,
            PFDisplay,
            PFGrid,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFSizing,
            css`
                .pf-c-description-list__description ak-action-button {
                    margin-right: 6px;
                    margin-bottom: 6px;
                }
                .ak-button-collection {
                    max-width: 12em;
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

    render(): TemplateResult {
        return html`<ak-page-header
                icon="pf-icon pf-icon-user"
                header=${msg(str`User ${this.user?.username || ""}`)}
                description=${this.user?.name || ""}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderUserCard(): TemplateResult {
        if (!this.user) {
            return html``;
        }
        const canImpersonate =
            rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanImpersonate) &&
            this.user.pk !== this.me?.user.pk;
        return html`
            <div class="pf-c-card__title">${msg("User Info")}</div>
            <div class="pf-c-card__body">
                <dl class="pf-c-description-list">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Username")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${this.user.username}</div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Name")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${this.user.name}</div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Email")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${this.user.email || "-"}</div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Last login")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                ${this.user.lastLogin?.toLocaleString()}
                            </div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Active")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                <ak-label
                                    color=${this.user.isActive ? PFColor.Green : PFColor.Orange}
                                ></ak-label>
                            </div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Superuser")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                <ak-label
                                    color=${this.user.isSuperuser ? PFColor.Green : PFColor.Orange}
                                ></ak-label>
                            </div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Actions")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description ak-button-collection">
                            <div class="pf-c-description-list__text">
                                <ak-forms-modal>
                                    <span slot="submit"> ${msg("Update")} </span>
                                    <span slot="header"> ${msg("Update User")} </span>
                                    <ak-user-form slot="form" .instancePk=${this.user.pk}>
                                    </ak-user-form>
                                    <button
                                        slot="trigger"
                                        class="pf-m-primary pf-c-button pf-m-block"
                                    >
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>
                                <ak-user-active-form
                                    .obj=${this.user}
                                    objectLabel=${msg("User")}
                                    .delete=${() => {
                                        return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                                            id: this.user?.pk || 0,
                                            patchedUserRequest: {
                                                isActive: !this.user?.isActive,
                                            },
                                        });
                                    }}
                                >
                                    <button
                                        slot="trigger"
                                        class="pf-c-button pf-m-warning pf-m-block"
                                    >
                                        <pf-tooltip
                                            position="top"
                                            content=${this.user.isActive
                                                ? msg("Lock the user out of this system")
                                                : msg(
                                                      "Allow the user to log in and use this system",
                                                  )}
                                        >
                                            ${this.user.isActive
                                                ? msg("Deactivate")
                                                : msg("Activate")}
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
                                                          id: this.user?.pk || 0,
                                                      })
                                                      .then(() => {
                                                          window.location.href = "/";
                                                      });
                                              }}
                                          >
                                              <pf-tooltip
                                                  position="top"
                                                  content=${msg(
                                                      "Temporarily assume the identity of this user",
                                                  )}
                                              >
                                                  ${msg("Impersonate")}
                                              </pf-tooltip>
                                          </ak-action-button>
                                      `
                                    : html``}
                            </div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Recovery")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text ak-button-collection">
                                <ak-forms-modal size=${PFSize.Medium}>
                                    <span slot="submit">${msg("Update password")}</span>
                                    <span slot="header">${msg("Update password")}</span>
                                    <ak-user-password-form
                                        slot="form"
                                        .instancePk=${this.user?.pk}
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
                                    .apiRequest=${() => {
                                        return new CoreApi(DEFAULT_CONFIG)
                                            .coreUsersRecoveryRetrieve({
                                                id: this.user?.pk || 0,
                                            })
                                            .then((rec) => {
                                                showMessage({
                                                    level: MessageLevel.success,
                                                    message: msg(
                                                        "Successfully generated recovery link",
                                                    ),
                                                    description: rec.link,
                                                });
                                            })
                                            .catch(() => {
                                                showMessage({
                                                    level: MessageLevel.error,
                                                    message: msg(
                                                        "To create a recovery link, the current tenant needs to have a recovery flow configured.",
                                                    ),
                                                    description: "",
                                                });
                                            });
                                    }}
                                >
                                    <pf-tooltip
                                        position="top"
                                        content=${msg(
                                            "Create a link for this user to reset their password",
                                        )}
                                    >
                                        ${msg("Reset Password")}
                                    </pf-tooltip>
                                </ak-action-button>
                            </div>
                        </dd>
                    </div>
                </dl>
            </div>
        `;
    }

    renderBody(): TemplateResult {
        if (!this.user) {
            return html``;
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
                        <ak-user-device-list userId=${this.user.pk}> </ak-user-device-list>
                    </div>
                </div>
            </section>
        </ak-tabs>`;
    }
}
