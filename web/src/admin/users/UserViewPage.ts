import "@goauthentik/admin/groups/RelatedGroupList";
import "@goauthentik/admin/users/UserActiveForm";
import "@goauthentik/admin/users/UserChart";
import "@goauthentik/admin/users/UserForm";
import "@goauthentik/admin/users/UserPasswordForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/PageHeader";
import { PFSize } from "@goauthentik/elements/Spinner";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/ObjectChangelog";
import "@goauthentik/elements/events/UserEvents";
import "@goauthentik/elements/forms/ModalForm";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/oauth/UserRefreshList";
import "@goauthentik/elements/user/SessionList";
import "@goauthentik/elements/user/UserConsentList";
import "@goauthentik/elements/user/UserDevicesList";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

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

import { CapabilitiesEnum, CoreApi, User } from "@goauthentik/api";

@customElement("ak-user-view")
export class UserViewPage extends AKElement {
    @property({ type: Number })
    set userId(id: number) {
        new CoreApi(DEFAULT_CONFIG)
            .coreUsersRetrieve({
                id: id,
            })
            .then((user) => {
                this.user = user;
            });
    }

    @property({ attribute: false })
    user?: User;

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
                header=${t`User ${this.user?.username || ""}`}
                description=${this.user?.name || ""}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderBody(): TemplateResult {
        if (!this.user) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${t`Overview`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${t`User Info`}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list pf-m-2-col">
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Username`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.user.username}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text">${t`Name`}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.user.name}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text">${t`Email`}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.user.email || "-"}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Last login`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.user.lastLogin?.toLocaleString()}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Active`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-label
                                                color=${this.user.isActive
                                                    ? PFColor.Green
                                                    : PFColor.Orange}
                                            ></ak-label>
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Superuser`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-label
                                                color=${this.user.isSuperuser
                                                    ? PFColor.Green
                                                    : PFColor.Orange}
                                            ></ak-label>
                                        </div>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-forms-modal>
                                <span slot="submit"> ${t`Update`} </span>
                                <span slot="header"> ${t`Update User`} </span>
                                <ak-user-form slot="form" .instancePk=${this.user.pk}>
                                </ak-user-form>
                                <button slot="trigger" class="pf-m-primary pf-c-button">
                                    ${t`Edit`}
                                </button>
                            </ak-forms-modal>
                        </div>
                        ${rootInterface()?.config?.capabilities.includes(
                            CapabilitiesEnum.CanImpersonate,
                        )
                            ? html`
                                  <div class="pf-c-card__footer">
                                      <a
                                          class="pf-c-button pf-m-tertiary"
                                          href="${`/-/impersonation/${this.user?.pk}/`}"
                                      >
                                          ${t`Impersonate`}
                                      </a>
                                  </div>
                              `
                            : html``}
                        <div class="pf-c-card__footer">
                            <ak-user-active-form
                                .obj=${this.user}
                                objectLabel=${t`User`}
                                .delete=${() => {
                                    return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                                        id: this.user?.pk || 0,
                                        patchedUserRequest: {
                                            isActive: !this.user?.isActive,
                                        },
                                    });
                                }}
                            >
                                <button slot="trigger" class="pf-c-button pf-m-warning">
                                    ${this.user.isActive ? t`Deactivate` : t`Activate`}
                                </button>
                            </ak-user-active-form>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-action-button
                                class="pf-m-secondary"
                                .apiRequest=${() => {
                                    return new CoreApi(DEFAULT_CONFIG)
                                        .coreUsersRecoveryRetrieve({
                                            id: this.user?.pk || 0,
                                        })
                                        .then((rec) => {
                                            showMessage({
                                                level: MessageLevel.success,
                                                message: t`Successfully generated recovery link`,
                                                description: rec.link,
                                            });
                                        })
                                        .catch(() => {
                                            showMessage({
                                                level: MessageLevel.error,
                                                message: t`To create a recovery link, the current tenant needs to have a recovery flow configured.`,
                                                description: "",
                                            });
                                        });
                                }}
                            >
                                ${t`Reset Password`}
                            </ak-action-button>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-forms-modal size=${PFSize.Medium}>
                                <span slot="submit">${t`Update password`}</span>
                                <span slot="header">${t`Update password`}</span>
                                <ak-user-password-form
                                    slot="form"
                                    .instancePk=${this.user?.pk}
                                ></ak-user-password-form>
                                <button slot="trigger" class="pf-c-button pf-m-secondary">
                                    ${t`Set password`}
                                </button>
                            </ak-forms-modal>
                        </div>
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                    >
                        <div class="pf-c-card__title">
                            ${t`Actions over the last week (per 8 hours)`}
                        </div>
                        <div class="pf-c-card__body">
                            <ak-charts-user userId=${this.user.pk || 0}> </ak-charts-user>
                        </div>
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${t`Changelog`}</div>
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
                data-tab-title="${t`Sessions`}"
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
                data-tab-title="${t`Groups`}"
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
                data-tab-title="${t`User events`}"
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
                data-tab-title="${t`Explicit Consent`}"
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
                data-tab-title="${t`OAuth Refresh Tokens`}"
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
                data-tab-title="${t`MFA Authenticators`}"
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
