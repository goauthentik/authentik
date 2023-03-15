import { DEFAULT_CONFIG, tenant } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_WS_MESSAGE,
} from "@goauthentik/common/constants";
import { configureSentry } from "@goauthentik/common/sentry";
import { UIConfig, UserDisplay, uiConfig } from "@goauthentik/common/ui/config";
import { autoDetectLanguage } from "@goauthentik/common/ui/locale";
import { me } from "@goauthentik/common/users";
import { first } from "@goauthentik/common/utils";
import { WebsocketClient } from "@goauthentik/common/ws";
import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import { DefaultTenant } from "@goauthentik/elements/sidebar/SidebarBrand";
import "@goauthentik/elements/sidebar/SidebarItem";
import { ROUTES } from "@goauthentik/user/Routes";

import { t } from "@lingui/macro";

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

import { CurrentTenant, EventsApi, SessionUser } from "@goauthentik/api";

autoDetectLanguage();

@customElement("ak-interface-user")
export class UserInterface extends Interface {
    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    ws: WebsocketClient;

    @property({ attribute: false })
    tenant: CurrentTenant = DefaultTenant;

    @property({ type: Number })
    notificationsCount = 0;

    @state()
    me?: SessionUser;

    @state()
    config?: UIConfig;

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
                .pf-c-page {
                    background-color: transparent;
                }
                .background-wrapper {
                    background-color: var(--pf-c-page--BackgroundColor) !important;
                }
                .display-none {
                    display: none;
                }
                .pf-c-brand {
                    min-height: 48px;
                    height: 48px;
                }
                .has-notifications {
                    color: #2b9af3;
                }
                .background-wrapper {
                    height: 100vh;
                    width: 100vw;
                    position: absolute;
                    z-index: -1;
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
        this.tenant = await tenant();
        this.me = await me();
        this.config = await uiConfig();
        const notifications = await new EventsApi(DEFAULT_CONFIG).eventsNotificationsList({
            seen: false,
            ordering: "-created",
            pageSize: 1,
            user: this.me.user.pk,
        });
        this.notificationsCount = notifications.pagination.count;
    }

    render(): TemplateResult {
        if (!this.config || !this.me) {
            return html``;
        }
        let userDisplay = "";
        switch (this.config.navbar.userDisplay) {
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
        return html`<div class="pf-c-page">
            <div class="background-wrapper" style="${this.config.theme.background}"></div>
            <header class="pf-c-page__header">
                <div class="pf-c-page__header-brand">
                    <a href="#/" class="pf-c-page__header-brand-link">
                        <img
                            class="pf-c-brand"
                            src="${first(this.tenant.brandingLogo, DefaultTenant.brandingLogo)}"
                            alt="${(this.tenant.brandingTitle, DefaultTenant.brandingTitle)}"
                        />
                    </a>
                </div>
                <div class="pf-c-page__header-tools">
                    <div class="pf-c-page__header-tools-group">
                        ${this.config.enabledFeatures.apiDrawer
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
                        ${this.config.enabledFeatures.notificationDrawer
                            ? html`<div
                                  class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg"
                              >
                                  <button
                                      class="pf-c-button pf-m-plain"
                                      type="button"
                                      aria-label="${t`Unread notifications`}"
                                      @click=${() => {
                                          this.notificationDrawerOpen =
                                              !this.notificationDrawerOpen;
                                          updateURLParams({
                                              notificationDrawerOpen: this.notificationDrawerOpen,
                                          });
                                      }}
                                  >
                                      <span
                                          class="pf-c-notification-badge ${this.notificationsCount >
                                          0
                                              ? "pf-m-unread"
                                              : ""}"
                                      >
                                          <i class="pf-icon-bell" aria-hidden="true"></i>
                                          <span class="pf-c-notification-badge__count"
                                              >${this.notificationsCount}</span
                                          >
                                      </span>
                                  </button>
                              </div> `
                            : html``}
                        ${this.config.enabledFeatures.settings
                            ? html` <div class="pf-c-page__header-tools-item">
                                  <a class="pf-c-button pf-m-plain" type="button" href="#/settings">
                                      <i class="fas fa-cog" aria-hidden="true"></i>
                                  </a>
                              </div>`
                            : html``}
                        <div class="pf-c-page__header-tools-item">
                            <a href="/flows/-/default/invalidation/" class="pf-c-button pf-m-plain">
                                <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                            </a>
                        </div>
                        ${this.me.user.isSuperuser
                            ? html`<a
                                  class="pf-c-button pf-m-primary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                                  href="/if/admin"
                              >
                                  ${t`Admin interface`}
                              </a>`
                            : html``}
                    </div>
                    ${this.me.original
                        ? html`<div class="pf-c-page__header-tools">
                              <div class="pf-c-page__header-tools-group">
                                  <a
                                      class="pf-c-button pf-m-warning pf-m-small"
                                      href=${`/-/impersonation/end/?back=${encodeURIComponent(
                                          `${window.location.pathname}#${window.location.hash}`,
                                      )}`}
                                  >
                                      ${t`Stop impersonation`}
                                  </a>
                              </div>
                          </div>`
                        : html``}
                    <div class="pf-c-page__header-tools-group">
                        <div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-md">
                            ${userDisplay}
                        </div>
                    </div>
                    <img class="pf-c-avatar" src=${this.me.user.avatar} alt="${t`Avatar image`}" />
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
                            class="pf-c-drawer__panel pf-m-width-33 ${this.notificationDrawerOpen
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
        </div>`;
    }
}
