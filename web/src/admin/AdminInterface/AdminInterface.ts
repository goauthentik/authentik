import { ROUTES } from "@goauthentik/admin/Routes";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
} from "@goauthentik/common/constants";
import { configureSentry } from "@goauthentik/common/sentry";
import { me } from "@goauthentik/common/users";
import { WebsocketClient } from "@goauthentik/common/ws";
import { EnterpriseAwareInterface } from "@goauthentik/elements/Interface";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/elements/enterprise/EnterpriseStatusBanner";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import "@goauthentik/elements/sidebar/SidebarItem";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AdminApi, SessionUser, UiThemeEnum, Version } from "@goauthentik/api";

import "./AdminSidebar";

@customElement("ak-interface-admin")
export class AdminInterface extends EnterpriseAwareInterface {
    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    ws: WebsocketClient;

    @state()
    version?: Version;

    @state()
    user?: SessionUser;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFButton,
            PFDrawer,
            css`
                .pf-c-page__main,
                .pf-c-drawer__content,
                .pf-c-page__drawer {
                    z-index: auto !important;
                    background-color: transparent;
                }
                .display-none {
                    display: none;
                }
                .pf-c-page {
                    background-color: var(--pf-c-page--BackgroundColor) !important;
                }
                /* Global page background colour */
                :host([theme="dark"]) .pf-c-page {
                    --pf-c-page--BackgroundColor: var(--ak-dark-background);
                }
            `,
        ];
    }

    constructor() {
        super();
        this.ws = new WebsocketClient();
        window.addEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, () => {
            this.notificationDrawerOpen = !this.notificationDrawerOpen;
            updateURLParams({
                notificationDrawerOpen: this.notificationDrawerOpen,
            });
        });
        window.addEventListener(EVENT_API_DRAWER_TOGGLE, () => {
            this.apiDrawerOpen = !this.apiDrawerOpen;
            updateURLParams({
                apiDrawerOpen: this.apiDrawerOpen,
            });
        });
    }

    async firstUpdated(): Promise<void> {
        configureSentry(true);
        this.version = await new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
        this.user = await me();
        const canAccessAdmin =
            this.user.user.isSuperuser ||
            // TODO: somehow add `access_admin_interface` to the API schema
            this.user.user.systemPermissions.includes("access_admin_interface");
        if (!canAccessAdmin && this.user.user.pk > 0) {
            window.location.assign("/if/user/");
        }
    }

    render(): TemplateResult {
        const sidebarClasses = {
            "pf-m-light": this.activeTheme === UiThemeEnum.Light,
        };

        const drawerOpen = this.notificationDrawerOpen || this.apiDrawerOpen;
        const drawerClasses = {
            "pf-m-expanded": drawerOpen,
            "pf-m-collapsed": !drawerOpen,
        };

        return html` <ak-locale-context>
            <div class="pf-c-page">
                <ak-admin-sidebar
                    class="pf-c-page__sidebar ${classMap(sidebarClasses)}"
                ></ak-admin-sidebar>
                <div class="pf-c-page__drawer">
                    <div class="pf-c-drawer ${classMap(drawerClasses)}">
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet
                                            role="main"
                                            class="pf-c-page__main"
                                            tabindex="-1"
                                            id="main-content"
                                            defaultUrl="/administration/overview"
                                            .routes=${ROUTES}
                                        >
                                        </ak-router-outlet>
                                    </main>
                                </div>
                            </div>
                            <ak-notification-drawer
                                class="pf-c-drawer__panel pf-m-width-33 ${this
                                    .notificationDrawerOpen
                                    ? ""
                                    : "display-none"}"
                                ?hidden=${!this.notificationDrawerOpen}
                            ></ak-notification-drawer>
                            <ak-api-drawer
                                class="pf-c-drawer__panel pf-m-width-33 ${this.apiDrawerOpen
                                    ? ""
                                    : "display-none"}"
                                ?hidden=${!this.apiDrawerOpen}
                            ></ak-api-drawer>
                        </div>
                    </div>
                </div></div
        ></ak-locale-context>`;
    }
}
