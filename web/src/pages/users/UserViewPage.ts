import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../authentik.css";

import "../../elements/forms/ModalForm";
import "./UserForm";
import "../../elements/buttons/ActionButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import "../../elements/events/ObjectChangelog";
import "../../elements/user/UserConsentList";
import "../../elements/oauth/UserCodeList";
import "../../elements/oauth/UserRefreshList";
import "../../elements/charts/UserChart";
import { Page } from "../../elements/Page";
import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EVENT_REFRESH } from "../../constants";
import { showMessage } from "../../elements/messages/MessageContainer";
import { MessageLevel } from "../../elements/messages/Message";

@customElement("ak-user-view")
export class UserViewPage extends Page {
    pageTitle(): string {
        return gettext(`User ${this.user?.username || ""}`);
    }
    pageDescription(): string | undefined {
        return this.user?.name || "";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-user";
    }

    @property({ type: Number })
    set userId(id: number) {
        new CoreApi(DEFAULT_CONFIG).coreUsersRead({
            id: id,
        }).then((user) => {
            this.user = user;
        });
    }

    @property({ attribute: false })
    user?: User;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFFlex, PFDisplay, PFGallery, PFContent, PFCard, PFDescriptionList, PFSizing, AKGlobal];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.user?.pk) return;
            this.userId = this.user?.pk;
        });
    }

    renderContent(): TemplateResult {
        if (!this.user) {
            return html``;
        }
        return html`<ak-tabs>
                <section slot="page-1" data-tab-title="${gettext("Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-l-gallery__item pf-m-4-col">
                            <div class="pf-c-card__title">
                                ${gettext("User Info")}
                            </div>
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Username")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.username}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Name")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.name}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Email")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.email}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Last login")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.lastLogin?.toLocaleString()}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Active")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <i class="fa ${this.user.isActive ? "fa-check-circle pf-m-success" : "fa-exclamation-triangle pf-m-warning"}"></i>
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Superuser")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <i class="fa ${this.user.isSuperuser ? "fa-check-circle pf-m-success" : "fa-exclamation-triangle pf-m-warning"}"></i>
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-forms-modal>
                                    <span slot="submit">
                                        ${gettext("Update")}
                                    </span>
                                    <span slot="header">
                                        ${gettext("Update User")}
                                    </span>
                                    <ak-user-form slot="form" .user=${this.user}>
                                    </ak-user-form>
                                    <button slot="trigger" class="pf-m-primary pf-c-button">
                                        ${gettext("Edit")}
                                    </button>
                                </ak-forms-modal>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-action-button
                                    .apiRequest=${() => {
                                        return new CoreApi(DEFAULT_CONFIG).coreUsersRecovery({
                                            id: this.user?.pk || 0,
                                        }).then(rec => {
                                            showMessage({
                                                level: MessageLevel.success,
                                                message: gettext("Successfully generated recovery link"),
                                                description: rec.link
                                            });
                                        });
                                    }}>
                                    ${gettext("Reset Password")}
                                </ak-action-button>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-gallery__item pf-m-4-col" style="grid-column-end: span 4;grid-row-end: span 2;">
                            <div class="pf-c-card__body">
                                <ak-charts-user>
                                </ak-charts-user>
                            </div>
                        </div>
                    </div>
                </section>
                <section slot="page-2" data-tab-title="${gettext("Changelog")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.user.pk || ""}
                                targetModelApp="authentik_core"
                                targetModelName="user">
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
                <section slot="page-3" data-tab-title="${gettext("Explicit Consent")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-consent-list .userId="${(this.user.pk || 0).toString()}">
                            </ak-user-consent-list>
                        </div>
                    </div>
                </section>
                <section slot="page-4" data-tab-title="${gettext("OAuth Authorization Codes")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-code-list .userId="${(this.user.pk || 0).toString()}">
                            </ak-user-oauth-code-list>
                        </div>
                    </div>
                </section>
                <section slot="page-5" data-tab-title="${gettext("OAuth Refresh Codes")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-refresh-list .userId="${(this.user.pk || 0).toString()}">
                            </ak-user-oauth-refresh-list>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
