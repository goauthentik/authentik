import { ROUTES } from "@goauthentik/admin/Routes";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
    VERSION,
} from "@goauthentik/common/constants";
import { configureSentry } from "@goauthentik/common/sentry";
import { me } from "@goauthentik/common/users";
import { WebsocketClient } from "@goauthentik/common/ws";
import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/elements/enterprise/EnterpriseStatusBanner";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "@goauthentik/elements/router/Route";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import "@goauthentik/elements/sidebar/SidebarItem";
import { spread } from "@open-wc/lit-helpers";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AdminApi,
    CapabilitiesEnum,
    CoreApi,
    SessionUser,
    UiThemeEnum,
    Version,
} from "@goauthentik/api";

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {
    @property({ type: Boolean })
    sidebarOpen = true;

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
        this.sidebarOpen = window.innerWidth >= 1280;
        window.addEventListener("resize", () => {
            this.sidebarOpen = window.innerWidth >= 1280;
        });
        window.addEventListener(EVENT_SIDEBAR_TOGGLE, () => {
            this.sidebarOpen = !this.sidebarOpen;
        });
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
        if (!this.user.user.isSuperuser && this.user.user.pk > 0) {
            window.location.assign("/if/user");
        }
    }

    render(): TemplateResult {
        return html` <ak-locale-context>
            <div class="pf-c-page">
                <ak-sidebar
                    class="pf-c-page__sidebar ${this.sidebarOpen
                        ? "pf-m-expanded"
                        : "pf-m-collapsed"} ${this.activeTheme === UiThemeEnum.Light
                        ? "pf-m-light"
                        : ""}"
                >
                    ${this.renderSidebarItems()}
                </ak-sidebar>
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

    renderSidebarItems(): TemplateResult {
        // The second attribute type is of string[] to help with the 'activeWhen' control, which was
        // commonplace and singular enough to merit its own handler.
        type SidebarEntry = [
            path: string | null,
            label: string,
            attributes?: Record<string, any> | string[] | null, // eslint-disable-line
            children?: SidebarEntry[],
        ];

        // prettier-ignore
        const sidebarContent: SidebarEntry[] = [
            ["/if/user/", msg("User interface"), { "?isAbsoluteLink": true, "?highlight": true }],
            [null, msg("Dashboards"), { "?expanded": true }, [
                ["/administration/overview", msg("Overview")],
                ["/administration/dashboard/users", msg("Users")],
                ["/administration/system-tasks", msg("System Tasks")]]],
            [null, msg("Applications"), null, [
                ["/core/providers", msg("Providers"), [`^/core/providers/(?<id>${ID_REGEX})$`]],
                ["/core/applications", msg("Applications"), [`^/core/applications/(?<slug>${SLUG_REGEX})$`]],
                ["/outpost/outposts", msg("Outposts")]]],
            [null, msg("Events"), null, [
                ["/events/log", msg("Logs"), [`^/events/log/(?<id>${UUID_REGEX})$`]],
                ["/events/rules", msg("Notification Rules")],
                ["/events/transports", msg("Notification Transports")]]],
            [null, msg("Customisation"), null, [
                ["/policy/policies", msg("Policies")],
                ["/core/property-mappings", msg("Property Mappings")],
                ["/blueprints/instances", msg("Blueprints")],
                ["/policy/reputation", msg("Reputation scores")]]],
            [null, msg("Flows and Stages"), null, [
                ["/flow/flows", msg("Flows"), [`^/flow/flows/(?<slug>${SLUG_REGEX})$`]],
                ["/flow/stages", msg("Stages")],
                ["/flow/stages/prompts", msg("Prompts")]]],
            [null, msg("Directory"), null, [
                ["/identity/users", msg("Users"), [`^/identity/users/(?<id>${ID_REGEX})$`]],
                ["/identity/groups", msg("Groups"), [`^/identity/groups/(?<id>${UUID_REGEX})$`]],
                ["/core/sources", msg("Federation and Social login"), [`^/core/sources/(?<slug>${SLUG_REGEX})$`]],
                ["/core/tokens", msg("Tokens and App passwords")],
                ["/flow/stages/invitations", msg("Invitations")]]],
            [null, msg("System"), null, [
                ["/core/tenants", msg("Tenants")],
                ["/crypto/certificates", msg("Certificates")],
                ["/outpost/integrations", msg("Outpost Integrations")]]]
        ];

        // Typescript requires the type here to correctly type the recursive path
        type SidebarRenderer = (_: SidebarEntry) => TemplateResult;

        const renderOneSidebarItem: SidebarRenderer = ([path, label, attributes, children]) => {
            const properties = Array.isArray(attributes)
                ? { ".activeWhen": attributes }
                : attributes ?? {};
            if (path) {
                properties["path"] = path;
            }
            return html`<ak-sidebar-item ${spread(properties)}>
                ${label ? html`<span slot="label">${label}</span>` : nothing}
                ${map(children, renderOneSidebarItem)}
            </ak-sidebar-item>`;
        };

        // prettier-ignore
        return html`
            ${this.renderNewVersionMessage()}
            ${this.renderImpersonationMessage()}
            ${map(sidebarContent, renderOneSidebarItem)}
            ${this.renderEnterpriseMessage()}
        `;
    }

    renderNewVersionMessage() {
        return this.version && this.version.versionCurrent !== VERSION
            ? html`
                  <ak-sidebar-item ?highlight=${true}>
                      <span slot="label"
                          >${msg("A newer version of the frontend is available.")}</span
                      >
                  </ak-sidebar-item>
              `
            : nothing;
    }

    renderImpersonationMessage() {
        return this.user?.original
            ? html`<ak-sidebar-item
                  ?highlight=${true}
                  @click=${() => {
                      new CoreApi(DEFAULT_CONFIG).coreUsersImpersonateEndRetrieve().then(() => {
                          window.location.reload();
                      });
                  }}
              >
                  <span slot="label"
                      >${msg(
                          str`You're currently impersonating ${this.user.user.username}. Click to stop.`,
                      )}</span
                  >
              </ak-sidebar-item>`
            : nothing;
    }

    renderEnterpriseMessage() {
        return this.config?.capabilities.includes(CapabilitiesEnum.IsEnterprise)
            ? html`
                  <ak-sidebar-item>
                      <span slot="label">${msg("Enterprise")}</span>
                      <ak-sidebar-item path="/enterprise/licenses">
                          <span slot="label">${msg("Licenses")}</span>
                      </ak-sidebar-item>
                  </ak-sidebar-item>
              `
            : nothing;
    }
}
