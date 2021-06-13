import "../elements/messages/MessageContainer";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { me } from "../api/Users";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "../elements/router/Route";
import "./locale";
import "../elements/sidebar/SidebarItem";
import { t } from "@lingui/macro";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";

import "../elements/router/RouterOutlet";
import "../elements/messages/MessageContainer";
import "../elements/notifications/NotificationDrawer";
import "../elements/Banner";
import "../elements/sidebar/Sidebar";
import { until } from "lit-html/directives/until";
import { EVENT_NOTIFICATION_TOGGLE, EVENT_SIDEBAR_TOGGLE, VERSION } from "../constants";
import { AdminApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../api/Config";


@customElement("ak-interface-admin")
export class AdminInterface extends LitElement {

    @property({type: Boolean})
    sidebarOpen = true;

    @property({type: Boolean})
    notificationOpen = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFButton, PFDrawer, css`
            .pf-c-page__main, .pf-c-drawer__content, .pf-c-page__drawer {
                z-index: auto !important;
            }
        `];
    }

    constructor() {
        super();
        this.sidebarOpen = window.innerWidth >= 1280;
        window.addEventListener("resize", () => {
            this.sidebarOpen = window.innerWidth >= 1280;
        });
        window.addEventListener(EVENT_SIDEBAR_TOGGLE, () => {
            this.sidebarOpen = !this.sidebarOpen;
        });
        window.addEventListener(EVENT_NOTIFICATION_TOGGLE, () => {
            this.notificationOpen = !this.notificationOpen;
        });
    }

    render(): TemplateResult {
        return html`
            ${until(new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve().then(version => {
                if (version.versionCurrent !== VERSION) {
                    return html`<ak-banner>
                        ${t`A newer version of the frontend is available.`}
                        <button @click=${() => { window.location.reload(true); }}>
                            ${t`Reload`}
                        </button>
                    </ak-banner>`;
                }
                return html``;
            }))}
            ${until(me().then((u) => {
                if (u.original) {
                    return html`<ak-banner>
                        ${t`You're currently impersonating ${u.user.username}.`}
                        <a href=${`/-/impersonation/end/?back=${window.location.pathname}%23${window.location.hash}`}>
                            ${t`Stop impersonation`}
                        </a>
                    </ak-banner>`;
                }
                return html``;
            }))}
            <div class="pf-c-page">
                <ak-sidebar class="pf-c-page__sidebar ${this.sidebarOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                    ${this.renderSidebarItems()}
                </ak-sidebar>
                <div class="pf-c-page__drawer">
                    <div class="pf-c-drawer ${this.notificationOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet role="main" class="pf-c-page__main" tabindex="-1" id="main-content" defaultUrl="/library">
                                        </ak-router-outlet>
                                    </main>
                                </div>
                            </div>
                            <ak-notification-drawer class="pf-c-drawer__panel pf-m-width-33">
                            </ak-notification-drawer>
                        </div>
                    </div>
                </div>
            </div>`;
    }

    renderSidebarItems(): TemplateResult {
        const superUserCondition = () => {
            return me().then(u => u.user.isSuperuser || false);
        };
        return html`
            <ak-sidebar-item path="/library">
                <span slot="label">${t`Library`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Monitor`}</span>
                <ak-sidebar-item path="/administration/overview">
                    <span slot="label">${t`Overview`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/administration/system-tasks">
                    <span slot="label">${t`System Tasks`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Resources`}</span>
                <ak-sidebar-item path="/core/applications" .activeWhen=${[`^/core/applications/(?<slug>${SLUG_REGEX})$`]}>
                    <span slot="label">${t`Applications`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/sources" .activeWhen=${[`^/core/sources/(?<slug>${SLUG_REGEX})$`]}>
                    <span slot="label">${t`Sources`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/providers" .activeWhen=${[`^/core/providers/(?<id>${ID_REGEX})$`]}>
                    <span slot="label">${t`Providers`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tenants">
                    <span slot="label">${t`Tenants`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Outposts`}</span>
                <ak-sidebar-item path="/outpost/outposts">
                    <span slot="label">${t`Outposts`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/outpost/service-connections">
                    <span slot="label">${t`Service Connections`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Events`}</span>
                <ak-sidebar-item path="/events/log" .activeWhen=${[`^/events/log/(?<id>${UUID_REGEX})$`]}>
                    <span slot="label">${t`Logs`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/events/rules">
                    <span slot="label">${t`Notification Rules`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/events/transports">
                    <span slot="label">${t`Notification Transports`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Customisation`}</span>
                <ak-sidebar-item path="/policy/policies">
                    <span slot="label">${t`Policies`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/policy/reputation/ip">
                    <span slot="label">${t`Reputation policy - IPs`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/policy/reputation/user">
                    <span slot="label">${t`Reputation policy - Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/property-mappings">
                    <span slot="label">${t`Property Mappings`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Flows`}</span>
                <ak-sidebar-item path="/flow/flows" .activeWhen=${[`^/flow/flows/(?<slug>${SLUG_REGEX})$`]}>
                    <span slot="label">${t`Flows`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages">
                    <span slot="label">${t`Stages`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/prompts">
                    <span slot="label">${t`Prompts`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/invitations">
                    <span slot="label">${t`Invitations`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Identity & Cryptography`}</span>
                <ak-sidebar-item path="/identity/users" .activeWhen=${[`^/identity/users/(?<id>${ID_REGEX})$`]}>
                    <span slot="label">${t`Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/identity/groups">
                    <span slot="label">${t`Groups`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/crypto/certificates">
                    <span slot="label">${t`Certificates`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tokens">
                    <span slot="label">${t`Tokens`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
        `;
    }

}
