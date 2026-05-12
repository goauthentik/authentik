import "#elements/banner/EnterpriseStatusBanner";
import "#elements/banner/VersionBanner";
import "#elements/sidebar/Sidebar";
import "#elements/sidebar/SidebarItem";
import "#elements/router/RouterOutlet";
import "#elements/commands/ak-command-palette";
import "#elements/commands/ak-command-palette-user-modal";

import {
    createAdminSidebarEnterpriseEntries,
    createAdminSidebarEntries,
    renderSidebarItems,
    SidebarEntry,
} from "./navigation/sidebar.js";

import { isAPIResultReady } from "#common/api/responses";
import { configureSentry } from "#common/sentry/index";
import { isGuest } from "#common/users";
import { WebsocketClient } from "#common/ws/WebSocketClient";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import {
    CommandPrefix,
    PaletteCommandDefinitionInit,
    PaletteCommandNamespace,
} from "#elements/commands/shared";
import { listen } from "#elements/decorators/listen";
import { renderDialog } from "#elements/dialogs";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithNotifications } from "#elements/mixins/notifications";
import { canAccessAdmin, WithSession } from "#elements/mixins/session";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import {
    DrawerState,
    persistDrawerParams,
    readDrawerParams,
    renderNotificationDrawerPanel,
} from "#elements/notifications/utils";
import { navigate } from "#elements/router/RouterOutlet";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#admin/ak-interface-admin.css";
import { ROUTES } from "#admin/Routes";

import { CapabilitiesEnum } from "@goauthentik/api";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail, msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, eventOptions, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { guard } from "lit/directives/guard.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-interface-admin")
export class AdminInterface extends WithCapabilitiesConfig(
    WithNotifications(WithSession(AuthenticatedInterface)),
) {
    //#region Styles

    public static readonly styles: CSSResult[] = [
        PFPage,
        PFButton,
        PFDrawer,
        PFNav,
        PFBanner,
        Styles,
    ];

    //#endregion

    //#region Public Properties

    @property({ type: Boolean, reflect: true, attribute: "sidebar" })
    public sidebarOpen = false;

    @property({ type: Array })
    public entries: readonly SidebarEntry[] = createAdminSidebarEntries();

    //#endregion

    //#region Public Methods

    public toggleSidebar = () => {
        this.sidebarOpen = !this.sidebarOpen;
    };

    public synchronizeSidebarEntries = () => {
        this.logger.debug("Synchronizing sidebar entries with current locale");
        this.entries = createAdminSidebarEntries();
    };

    //#endregion

    //#region Event Listeners

    #sidebarMatcher: MediaQueryList;
    #sidebarMediaQueryListener = (event: MediaQueryListEvent) => {
        this.sidebarOpen = event.matches;
    };

    @eventOptions({ passive: true })
    protected routeChangeListener() {
        this.sidebarOpen = this.#sidebarMatcher.matches;
    }

    @state()
    protected drawer: DrawerState = readDrawerParams();

    @listen(AKDrawerChangeEvent, { target: window })
    protected drawerListener = (event: AKDrawerChangeEvent) => {
        this.drawer = event.drawer;
        persistDrawerParams(event.drawer);
    };

    @listen(LOCALE_STATUS_EVENT, { target: window })
    localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status === "ready") {
            this.synchronizeSidebarEntries();
        }
    };

    //#endregion

    //#region Lifecycle

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        this.#sidebarMatcher = window.matchMedia("(width > 1210px)");
        this.sidebarOpen = this.#sidebarMatcher.matches;
    }

    #refreshCommandsFrameID = -1;

    #refreshCommands = () => {
        const commands: PaletteCommandDefinitionInit[] = [
            {
                label: msg("Create a new application..."),
                action: () => navigate("/core/applications", { createWizard: true }),
                group: msg("Applications"),
            },
            {
                namespace: PaletteCommandNamespace.Navigation,
                label: msg("Check the logs"),
                action: () => navigate("/events/log"),
                group: msg("Events"),
            },
            {
                namespace: PaletteCommandNamespace.Navigation,
                label: msg("Manage users"),
                action: () => navigate("/identity/users"),
                group: msg("Users"),
            },
            ...this.entries.flatMap(([, label, , children]) => [
                ...(children ?? []).map(
                    ([path, childLabel]): PaletteCommandDefinitionInit => ({
                        namespace: PaletteCommandNamespace.Navigation,
                        label: childLabel,
                        group: label,
                        action: () => {
                            navigate(path!);
                        },
                    }),
                ),
            ]),
            {
                namespace: PaletteCommandNamespace.Search,
                label: msg("Username or email address..."),
                prefix: CommandPrefix.SearchFor(),
                group: msg("Users"),
                keywords: [msg("search"), msg("find")],
                action: async (data, event) => {
                    event?.stopPropagation();

                    const userPalette = this.ownerDocument.createElement(
                        "ak-command-palette-user-modal",
                    );

                    renderDialog(userPalette, {
                        parentElement: this,
                    });

                    userPalette.show();
                },
            },
        ];

        this.commandPalette.modal.setCommands(
            commands.map((command) => ({ namespace: PaletteCommandNamespace.Action, ...command })),
        );
    };

    public connectedCallback() {
        super.connectedCallback();

        this.#sidebarMatcher.addEventListener("change", this.#sidebarMediaQueryListener, {
            passive: true,
        });
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();

        cancelAnimationFrame(this.#refreshCommandsFrameID);

        this.#sidebarMatcher.removeEventListener("change", this.#sidebarMediaQueryListener);

        WebsocketClient.close();
    }

    public firstUpdated(changedProperties: PropertyValues<this>): void {
        super.firstUpdated(changedProperties);

        this.#refreshCommandsFrameID = requestAnimationFrame(this.#refreshCommands);
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("session") && isAPIResultReady(this.session)) {
            if (!isGuest(this.session.user) && !canAccessAdmin(this.session.user)) {
                window.location.assign("/if/user/");
            }
        }
    }

    //#endregion

    //#region Rendering

    protected override render(): TemplateResult {
        if (!isAPIResultReady(this.session) || !canAccessAdmin(this.session.user)) {
            return html`<slot></slot>`;
        }

        const sidebarClasses = {
            "pf-c-page__sidebar": true,
            "pf-m-expanded": this.sidebarOpen,
            "pf-m-collapsed": !this.sidebarOpen,
        };

        const openDrawerCount = (this.drawer.notifications ? 1 : 0) + (this.drawer.api ? 1 : 0);
        const drawerClasses = {
            "pf-m-expanded": openDrawerCount !== 0,
            "pf-m-collapsed": openDrawerCount === 0,
        };

        return html`<div class="pf-c-page">
                <ak-page-navbar>
                    <button
                        slot="toggle"
                        aria-controls="global-nav"
                        class="pf-c-button pf-m-plain"
                        @click=${this.toggleSidebar}
                        aria-label=${this.sidebarOpen
                            ? msg("Collapse navigation")
                            : msg("Expand navigation")}
                        aria-expanded=${this.sidebarOpen ? "true" : "false"}
                    >
                        <i aria-hidden="true" class="fas fa-bars"></i>
                    </button>

                    ${this.renderCommandPaletteButton()}
                    <ak-version-banner></ak-version-banner>
                    <ak-enterprise-status interface="admin"></ak-enterprise-status>
                </ak-page-navbar>

                <ak-sidebar ?hidden=${!this.sidebarOpen} class="${classMap(sidebarClasses)}"
                    >${renderSidebarItems(this.entries)}
                    ${this.can(CapabilitiesEnum.IsEnterprise)
                        ? renderSidebarItems(createAdminSidebarEnterpriseEntries())
                        : nothing}
                </ak-sidebar>

                <div class="pf-c-page__drawer">
                    <div class="pf-c-drawer ${classMap(drawerClasses)}">
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <ak-router-outlet
                                        role="presentation"
                                        class="pf-c-page__main"
                                        tabindex="-1"
                                        id="main-content"
                                        default-url="/administration/overview"
                                        .routes=${ROUTES}
                                        @ak-route-change=${this.routeChangeListener}
                                    >
                                    </ak-router-outlet>
                                </div>
                            </div>
                            ${renderNotificationDrawerPanel(this.drawer)}
                        </div>
                    </div>

                    <div
                        class="pf-c-page__sidebar-backdrop"
                        aria-label=${this.sidebarOpen ? msg("Close sidebar") : msg("Open sidebar")}
                        @click=${this.toggleSidebar}
                        role="button"
                        tabindex="0"
                    ></div>
                </div>
            </div>
            ${this.commandPalette}`;
    }

    protected renderCommandPaletteButton(): SlottedTemplateResult {
        return guard([this.commandPalette.showListener], () => {
            const macOS = navigator.platform.toUpperCase().indexOf("MAC") >= 0;

            const primaryModifierKey = macOS ? "⌘" : "Ctrl";

            return html`<button
                slot="nav-buttons"
                @click=${this.commandPalette.showListener}
                class="pf-c-button pf-m-plain command-palette-trigger"
                aria-label=${msg("Open Command Palette", {
                    id: "command-palette-trigger-label",
                    desc: "Label for the button that opens the command palette",
                })}
            >
                <pf-tooltip position="top-end">
                    <div slot="content" class="ak-tooltip__content--inline">
                        ${msg("Open Command Palette", {
                            id: "command-palette-trigger-tooltip",
                            desc: "Tooltip for the button that opens the command palette",
                        })}
                        <div class="ak-c-kbd"><kbd>${primaryModifierKey}</kbd> + <kbd>K</kbd></div>
                    </div>

                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                        class="ak-c-vector-icon"
                        role="img"
                        viewBox="0 0 32 32"
                    >
                        <path
                            d="M26 4.01H6a2 2 0 0 0-2 2v20a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-20a2 2 0 0 0-2-2m0 2v4H6v-4Zm-20 20v-14h20v14Z"
                        />
                        <path d="m10.76 16.18 2.82 2.83-2.82 2.83 1.41 1.41 4.24-4.24-4.24-4.24z" />
                    </svg>
                </pf-tooltip>
            </button>`;
        });
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-admin": AdminInterface;
    }
}
