import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_WS_MESSAGE,
} from "@goauthentik/common/constants";
import { configureSentry } from "@goauthentik/common/sentry";
import { UserDisplay } from "@goauthentik/common/ui/config";
import { me } from "@goauthentik/common/users";
import { first } from "@goauthentik/common/utils";
import { WebsocketClient } from "@goauthentik/common/ws";
import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/enterprise/EnterpriseStatusBanner";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import { DefaultTenant } from "@goauthentik/elements/sidebar/SidebarBrand";
import "@goauthentik/elements/sidebar/SidebarItem";
import { ROUTES } from "@goauthentik/user/Routes";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import { CoreApi, EventsApi, SessionUser } from "@goauthentik/api";

@customElement("ak-interface-user")
export class UserInterface extends Interface {
    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    ws: WebsocketClient;

    @property({ type: Number })
    notificationsCount = 0;

    @state()
    me?: SessionUser;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFDisplay,
            PFBrand,
            PFPage,
            PFAvatar,
            PFButton,
            PFDrawer,
            PFDropdown,
            PFNotificationBadge,
            css`
                .pf-c-page__main,
                .pf-c-drawer__content,
                .pf-c-page__drawer {
                    z-index: auto !important;
                    background-color: transparent !important;
                }
                .pf-c-page__header {
                    background-color: transparent !important;
                    box-shadow: none !important;
                    color: black !important;
                }
                :host([theme="dark"]) .pf-c-page__header {
                    color: var(--ak-dark-foreground) !important;
                }
                .pf-c-page__header-tools-item .fas,
                .pf-c-notification-badge__count,
                .pf-c-page__header-tools-group .pf-c-button {
                    color: var(--ak-global--Color--100) !important;
                }
                .pf-c-page {
                    background-color: transparent;
                }
                .display-none {
                    display: none;
                }
                .pf-c-brand {
                    min-height: 32px;
                    height: 32px;
                }
                .has-notifications {
                    color: #2b9af3;
                }
                .background-wrapper {
                    height: 100vh;
                    width: 100%;
                    position: fixed;
                    z-index: -1;
                    top: 0;
                    left: 0;
                    background-color: var(--pf-c-page--BackgroundColor) !important;
                }
                .background-default-slant {
                    background-color: white; /*var(--ak-accent);*/
                    clip-path: polygon(0 0, 100% 0, 100% 100%, 0 calc(100% - 5vw));
                    height: 50vh;
                }
                :host([theme="dark"]) .background-default-slant {
                    background-color: black;
                }
                ak-locale-context {
                    display: flex;
                    flex-direction: column;
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
        window.addEventListener(EVENT_WS_MESSAGE, () => {
            this.firstUpdated();
        });
        configureSentry(true);
    }

    async firstUpdated(): Promise<void> {
        this.me = await me();
        const notifications = await new EventsApi(DEFAULT_CONFIG).eventsNotificationsList({
            seen: false,
            ordering: "-created",
            pageSize: 1,
            user: this.me.user.pk,
        });
        this.notificationsCount = notifications.pagination.count;
    }

    render(): TemplateResult {
        if (!this.uiConfig || !this.me) {
            return html``;
        }
        let userDisplay = "";
        switch (this.uiConfig.navbar.userDisplay) {
            case UserDisplay.username:
                userDisplay = this.me.user.username;
                break;
            case UserDisplay.name:
                userDisplay = this.me.user.name;
                break;
            case UserDisplay.email:
                userDisplay = this.me.user.email || "";
                break;
            default:
                userDisplay = this.me.user.username;
        }
        return html` <ak-locale-context>
            <ak-enterprise-status interface="user"></ak-enterprise-status>
            <div class="pf-c-page">
                <div class="background-wrapper" style="${this.uiConfig.theme.background}">
                    ${this.uiConfig.theme.background === ""
                        ? html`<div class="background-default-slant"></div>`
                        : html``}
                </div>
                <header class="pf-c-page__header">
                    <div class="pf-c-page__header-brand">
                        <a href="#/" class="pf-c-page__header-brand-link">
                            <img
                                class="pf-c-brand"
                                src="${first(
                                    this.tenant?.brandingLogo,
                                    DefaultTenant.brandingLogo,
                                )}"
                                alt="${(this.tenant?.brandingTitle, DefaultTenant.brandingTitle)}"
                            />
                        </a>
                    </div>
                    <div class="pf-c-page__header-tools">
                        <div class="pf-c-page__header-tools-group">
                            ${this.uiConfig.enabledFeatures.apiDrawer
                                ? html`<div
                                      class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg"
                                  >
                                      <button
                                          class="pf-c-button pf-m-plain"
                                          type="button"
                                          @click=${() => {
                                              this.apiDrawerOpen = !this.apiDrawerOpen;
                                              updateURLParams({
                                                  apiDrawerOpen: this.apiDrawerOpen,
                                              });
                                          }}
                                      >
                                          <i class="fas fa-code" aria-hidden="true"></i>
                                      </button>
                                  </div>`
                                : html``}
                            ${this.uiConfig.enabledFeatures.notificationDrawer
                                ? html`<div
                                      class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg"
                                  >
                                      <button
                                          class="pf-c-button pf-m-plain"
                                          type="button"
                                          aria-label="${msg("Unread notifications")}"
                                          @click=${() => {
                                              this.notificationDrawerOpen =
                                                  !this.notificationDrawerOpen;
                                              updateURLParams({
                                                  notificationDrawerOpen:
                                                      this.notificationDrawerOpen,
                                              });
                                          }}
                                      >
                                          <span
                                              class="pf-c-notification-badge ${this
                                                  .notificationsCount > 0
                                                  ? "pf-m-unread"
                                                  : ""}"
                                          >
                                              <i class="fas fa-bell" aria-hidden="true"></i>
                                              <span class="pf-c-notification-badge__count"
                                                  >${this.notificationsCount}</span
                                              >
                                          </span>
                                      </button>
                                  </div> `
                                : html``}
                            ${this.uiConfig.enabledFeatures.settings
                                ? html` <div class="pf-c-page__header-tools-item">
                                      <a
                                          class="pf-c-button pf-m-plain"
                                          type="button"
                                          href="#/settings"
                                      >
                                          <i class="fas fa-cog" aria-hidden="true"></i>
                                      </a>
                                  </div>`
                                : html``}
                            <div class="pf-c-page__header-tools-item">
                                <a
                                    href="/flows/-/default/invalidation/"
                                    class="pf-c-button pf-m-plain"
                                >
                                    <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                                </a>
                            </div>
                            ${this.me.user.isSuperuser
                                ? html`<a
                                      class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                                      href="/if/admin"
                                  >
                                      ${msg("Admin interface")}
                                  </a>`
                                : html``}
                        </div>
                        ${this.me.original
                            ? html`&nbsp;
                                  <div class="pf-c-page__header-tools">
                                      <div class="pf-c-page__header-tools-group">
                                          <ak-action-button
                                              class="pf-m-warning pf-m-small"
                                              .apiRequest=${() => {
                                                  return new CoreApi(DEFAULT_CONFIG)
                                                      .coreUsersImpersonateEndRetrieve()
                                                      .then(() => {
                                                          window.location.reload();
                                                      });
                                              }}
                                          >
                                              ${msg("Stop impersonation")}
                                          </ak-action-button>
                                      </div>
                                  </div>`
                            : html``}
                        <div class="pf-c-page__header-tools-group">
                            <div
                                class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-md"
                            >
                                ${userDisplay}
                            </div>
                        </div>
                        <img
                            class="pf-c-avatar"
                            src=${this.me.user.avatar}
                            alt="${msg("Avatar image")}"
                        />
                    </div>
                </header>
                <div class="pf-c-page__drawer">
                    <div
                        class="pf-c-drawer ${this.notificationDrawerOpen || this.apiDrawerOpen
                            ? "pf-m-expanded"
                            : "pf-m-collapsed"}"
                    >
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet
                                            role="main"
                                            class="pf-l-bullseye__item pf-c-page__main"
                                            tabindex="-1"
                                            id="main-content"
                                            defaultUrl="/library"
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
                </div>
            </div>
        </ak-locale-context>`;
    }
}
