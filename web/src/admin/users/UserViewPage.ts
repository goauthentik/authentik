import "#admin/groups/RelatedGroupList";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/users/UserApplicationsTab";
import "#admin/users/UserCredentialsTab";
import "#admin/users/UserOverviewTab";
import "#admin/users/UserRolesTab";
import "#admin/events/UserEvents";
import "#elements/Tabs";

import { aki } from "#common/api/client";
import { AKRefreshEvent } from "#common/events";
import { formatDisambiguatedUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithLocale } from "#elements/mixins/locale";
import { WithSession } from "#elements/mixins/session";

import { setPageDetails } from "#components/ak-page-navbar";

import { CapabilitiesEnum, CoreApi, ModelEnum, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-user-view")
export class UserViewPage extends WithLicenseSummary(
    WithLocale(WithBrandConfig(WithCapabilitiesConfig(WithSession(AKElement)))),
) {
    #api = aki(CoreApi);

    @property({ type: Number, useDefault: true })
    public userId: number | null = null;

    @property({ attribute: false, useDefault: true })
    public user: User | null = null;

    @state()
    private activatedTabs = new Set<string>(["page-overview"]);

    static styles = [PFPage, PFContent, PFCard];

    @listen(AKRefreshEvent)
    public refresh = () => {
        if (!this.userId) {
            return;
        }

        return this.#api
            .coreUsersRetrieve({
                id: this.userId,
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
                header: username || msg("User"),
                description:
                    name || email
                        ? formatDisambiguatedUserDisplayName(
                              { name, email },
                              this.activeLanguageTag,
                          )
                        : null,
            });
        }
    }

    protected activateTab(tab: string) {
        if (this.activatedTabs.has(tab)) {
            return;
        }

        this.activatedTabs = new Set([...this.activatedTabs, tab]);
    }

    protected renderWhenActive(tab: string, content: unknown) {
        return this.activatedTabs.has(tab) ? content : null;
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
                    @activate=${() => this.activateTab("page-overview")}
                >
                    <ak-user-overview-tab
                        .user=${this.user}
                        .currentUserPk=${this.currentUser?.pk}
                        .canImpersonate=${this.can(CapabilitiesEnum.CanImpersonate)}
                        .hasEnterpriseLicense=${this.hasEnterpriseLicense}
                        .brandHasRecoveryFlow=${!!this.brand.flowRecovery}
                    ></ak-user-overview-tab>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-groups"
                    id="page-groups"
                    aria-label=${msg("Groups")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    @activate=${() => this.activateTab("page-groups")}
                >
                    ${this.renderWhenActive(
                        "page-groups",
                        html`<div class="pf-c-card">
                            <ak-group-related-list .targetUser=${this.user}></ak-group-related-list>
                        </div>`,
                    )}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-roles"
                    id="page-roles"
                    aria-label=${msg("Roles")}
                    @activate=${() => this.activateTab("page-roles")}
                >
                    ${this.renderWhenActive(
                        "page-roles",
                        html`<ak-user-roles-tab .user=${this.user}></ak-user-roles-tab>`,
                    )}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-events"
                    id="page-events"
                    aria-label=${msg("User events")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    @activate=${() => this.activateTab("page-events")}
                >
                    ${this.renderWhenActive(
                        "page-events",
                        html`<div class="pf-c-card">
                            <ak-events-user targetUser=${this.user.username}></ak-events-user>
                        </div>`,
                    )}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-credentials"
                    id="page-credentials"
                    aria-label=${msg("Credentials / Tokens")}
                    @activate=${() => this.activateTab("page-credentials")}
                >
                    ${this.renderWhenActive(
                        "page-credentials",
                        html`<ak-user-credentials-tab
                            .user=${this.user}
                        ></ak-user-credentials-tab>`,
                    )}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-applications"
                    id="page-applications"
                    aria-label=${msg("Applications")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    @activate=${() => this.activateTab("page-applications")}
                >
                    ${this.renderWhenActive(
                        "page-applications",
                        html`<ak-user-applications-tab
                            .user=${this.user}
                        ></ak-user-applications-tab>`,
                    )}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label=${msg("Permissions")}
                    @activate=${() => this.activateTab("page-permissions")}
                >
                    ${this.renderWhenActive(
                        "page-permissions",
                        html`<ak-rbac-object-permission-page
                            model=${ModelEnum.AuthentikCoreUser}
                            objectPk=${this.user.pk}
                        ></ak-rbac-object-permission-page>`,
                    )}
                </div>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-view": UserViewPage;
    }
}
