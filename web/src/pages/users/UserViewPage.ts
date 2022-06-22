import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "../../authentik.css";
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

import { DEFAULT_CONFIG, config } from "../../api/Config";
import { EVENT_REFRESH } from "../../constants";
import "../../elements/CodeMirror";
import { PFColor } from "../../elements/Label";
import "../../elements/PageHeader";
import { PFSize } from "../../elements/Spinner";
import "../../elements/Tabs";
import "../../elements/buttons/ActionButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/charts/UserChart";
import "../../elements/events/ObjectChangelog";
import "../../elements/events/UserEvents";
import "../../elements/forms/ModalForm";
import { MessageLevel } from "../../elements/messages/Message";
import { showMessage } from "../../elements/messages/MessageContainer";
import "../../elements/oauth/UserRefreshList";
import "../../elements/user/SessionList";
import "../../elements/user/UserConsentList";
import "../groups/RelatedGroupList";
import "./UserActiveForm";
import "./UserForm";
import "./UserPasswordForm";

@customElement("ak-user-view")
export class UserViewPage extends LitElement {
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
            AKGlobal,
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
                        ${until(
                            config().then((config) => {
                                if (config.capabilities.includes(CapabilitiesEnum.Impersonate)) {
                                    return html` <div class="pf-c-card__footer">
                                        <a
                                            class="pf-c-button pf-m-tertiary"
                                            href="${`/-/impersonation/${this.user?.pk}/`}"
                                        >
                                            ${t`Impersonate`}
                                        </a>
                                    </div>`;
                                }
                                return html``;
                            }),
                        )}
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
                        <div class="pf-c-card__title">${t`Actions over the last 24 hours`}</div>
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
                        <ak-group-related-list targetUser=${this.user.pk}> </ak-group-related-list>
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
                data-tab-title="${t`OAuth Refresh Codes`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-user-oauth-refresh-list userId=${this.user.pk}>
                        </ak-user-oauth-refresh-list>
                    </div>
                </div>
            </section>
        </ak-tabs>`;
    }
}
