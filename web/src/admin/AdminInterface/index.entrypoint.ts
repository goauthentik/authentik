import "#admin/AdminInterface/AboutModal";
import "#admin/AdminInterface/AdminRouterOutlet";
import "#elements/banner/EnterpriseStatusBanner";
import "#elements/banner/VersionBanner";
import "#elements/messages/MessageContainer";
import "#elements/sidebar/Sidebar";
import "#elements/sidebar/SidebarItem";

import {
    createAdminSidebarEnterpriseEntries,
    createAdminSidebarEntries,
    SidebarEntry,
} from "./AdminSidebar.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { isAPIResultReady } from "#common/api/responses";
import { configureSentry } from "#common/sentry/index";
import { isGuest } from "#common/users";
import { WebsocketClient } from "#common/ws/WebSocketClient";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { listen } from "#elements/decorators/listen";
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
import { SidebarPinToggleEvent } from "#elements/sidebar/SidebarItem";

import { PageNavMenuToggle } from "#components/ak-page-navbar";

import type { AboutModal } from "#admin/AdminInterface/AboutModal";
import Styles from "#admin/AdminInterface/index.entrypoint.css";
import { ROUTES } from "#admin/Routes";

import { CapabilitiesEnum, CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

@customElement("ak-interface-admin")
export class AdminInterface extends WithCapabilitiesConfig(
    WithNotifications(WithSession(AuthenticatedInterface)),
) {
    //#region Styles

    public static readonly styles: CSSResult[] = [
        // ---
        PFPage,
        PFButton,
        PFDrawer,
        PFNav,
        Styles,
    ];

    //#endregion

    //#region Properties

    @query("ak-about-modal")
    public aboutModal?: AboutModal;

    @property({ type: Boolean, reflect: true })
    public sidebarOpen = false;

    #onPageNavMenuEvent = (event: PageNavMenuToggle) => {
        this.sidebarOpen = event.open;
    };

    #sidebarMatcher: MediaQueryList;
    #sidebarMediaQueryListener = (event: MediaQueryListEvent) => {
        this.sidebarOpen = event.matches;
    };

    //#endregion

    @state()
    protected drawer: DrawerState = readDrawerParams();

    @listen(AKDrawerChangeEvent)
    protected drawerListener = (event: AKDrawerChangeEvent) => {
        this.drawer = event.drawer;
        persistDrawerParams(event.drawer);
    };

    #onPinToggleEvent = (event: Event) => {
        const pinEvent = event as SidebarPinToggleEvent;
        this.handlePinToggle(pinEvent.path, pinEvent.pinned);
    };

    //#region Lifecycle

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        this.#sidebarMatcher = window.matchMedia("(min-width: 1200px)");
        this.sidebarOpen = this.#sidebarMatcher.matches;

        this.addEventListener(PageNavMenuToggle.eventName, this.#onPageNavMenuEvent, {
            passive: true,
        });
    }

    public connectedCallback() {
        super.connectedCallback();

        this.#sidebarMatcher.addEventListener("change", this.#sidebarMediaQueryListener, {
            passive: true,
        });
        this.addEventListener(SidebarPinToggleEvent.eventName, this.#onPinToggleEvent);
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();

        this.#sidebarMatcher.removeEventListener("change", this.#sidebarMediaQueryListener);
        this.removeEventListener(SidebarPinToggleEvent.eventName, this.#onPinToggleEvent);

        WebsocketClient.close();
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("session") && isAPIResultReady(this.session)) {
            if (!isGuest(this.session.user) && !canAccessAdmin(this.session.user)) {
                window.location.assign("/if/user/");
            }
        }
    }

    /**
     * Check if the current user has a specific permission.
     * Superusers have all permissions.
     */
    private hasPermission(permission: string): boolean {
        const user = this.currentUser;
        if (!user) return false;
        if (user.isSuperuser) return true;
        return user.systemPermissions?.includes(permission) ?? false;
    }

    /**
     * Recursively filter sidebar entries based on user permissions.
     * Removes entries the user doesn't have permission to access.
     * Also removes parent sections if all their children are filtered out.
     * Optionally excludes pinned entries from their original location.
     */
    private filterSidebarEntries(
        entries: readonly SidebarEntry[],
        excludePinned = false,
    ): SidebarEntry[] {
        return entries
            .map((entry): SidebarEntry | null => {
                const [path, label, attributes, children, requiredPermission] = entry;

                // Check permission for this entry
                if (requiredPermission && !this.hasPermission(requiredPermission)) {
                    return null;
                }

                // Exclude pinned entries from their original location
                if (excludePinned && path && this.pinnedPaths.includes(path)) {
                    return null;
                }

                // Recursively filter children
                const filteredChildren = children
                    ? this.filterSidebarEntries(children, excludePinned)
                    : undefined;

                // Hide section headers if all children are filtered out
                if (children && filteredChildren && filteredChildren.length === 0) {
                    return null;
                }

                return [path, label, attributes, filteredChildren, requiredPermission];
            })
            .filter((entry): entry is SidebarEntry => entry !== null);
    }

    /**
     * Get the list of pinned tab paths from user settings.
     */
    private get pinnedPaths(): string[] {
        // Read directly from user settings, not uiConfig, since uiConfig
        // is only populated via refreshSession() which may not have been called yet
        const settings = this.currentUser?.settings as Record<string, unknown> | undefined;
        const adminSettings = settings?.admin as Record<string, unknown> | undefined;
        return (adminSettings?.pinnedTabs as string[]) ?? [];
    }

    /**
     * Handle pin toggle event by updating user settings.
     */
    private async handlePinToggle(path: string, pinned: boolean): Promise<void> {
        const user = this.currentUser;
        if (!user) return;

        const currentPinned = [...this.pinnedPaths];

        if (pinned && !currentPinned.includes(path)) {
            currentPinned.push(path);
        } else if (!pinned) {
            const index = currentPinned.indexOf(path);
            if (index > -1) currentPinned.splice(index, 1);
        }

        // Update user settings via API
        // We need to fetch the full user first to get their attributes
        try {
            const fullUser = await new CoreApi(DEFAULT_CONFIG).coreUsersRetrieve({
                id: user.pk,
            });

            await new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                id: user.pk,
                patchedUserRequest: {
                    attributes: {
                        ...(fullUser.attributes ?? {}),
                        settings: {
                            ...((fullUser.attributes?.settings as Record<string, unknown>) ?? {}),
                            admin: {
                                ...((fullUser.attributes?.settings as Record<string, unknown>)
                                    ?.admin ?? {}),
                                pinnedTabs: currentPinned,
                            },
                        },
                    },
                },
            });

            // Refresh session to update uiConfig
            await this.refreshSession();
        } catch (error) {
            console.error("Failed to update pinned tabs:", error);
        }
    }

    /**
     * Find sidebar entries by their paths from a nested entry structure.
     */
    private findEntriesByPaths(
        entries: readonly SidebarEntry[],
        paths: string[],
    ): SidebarEntry[] {
        const result: SidebarEntry[] = [];

        for (const entry of entries) {
            const [path, , , children] = entry;
            if (path && paths.includes(path)) {
                result.push(entry);
            }
            if (children) {
                result.push(...this.findEntriesByPaths(children, paths));
            }
        }

        return result;
    }

    /**
     * Render a sidebar entry with pinnable/pinned state.
     */
    private renderSidebarEntry(entry: SidebarEntry): TemplateResult {
        const [path, label, attributes, children] = entry;

        const properties: Record<string, unknown> = Array.isArray(attributes)
            ? { ".activeWhen": attributes }
            : { ...(attributes ?? {}) };

        if (path) {
            properties.path = path;
            // Leaf items (no children) are pinnable
            if (!children) {
                properties.pinnable = true;
                properties.pinned = this.pinnedPaths.includes(path);
            }
        }

        return html`<ak-sidebar-item
            exportparts="list-item, link"
            label=${label}
            .path=${path}
            .pinnable=${properties.pinnable ?? false}
            .pinned=${properties.pinned ?? false}
            ?expanded=${properties["?expanded"]}
            ?enterprise=${properties.enterprise}
            .activeWhen=${properties[".activeWhen"] ?? []}
        >
            ${children ? children.map((child) => this.renderSidebarEntry(child)) : nothing}
        </ak-sidebar-item>`;
    }

    /**
     * Render the pinned section at the top of the sidebar.
     */
    private renderPinnedSection(): TemplateResult | typeof nothing {
        if (this.pinnedPaths.length === 0) return nothing;

        const allEntries = [
            ...createAdminSidebarEntries(),
            ...(this.can(CapabilitiesEnum.IsEnterprise)
                ? createAdminSidebarEnterpriseEntries()
                : []),
        ];

        const pinnedEntries = this.findEntriesByPaths(allEntries, this.pinnedPaths);
        // Filter by permissions
        const filteredPinned = pinnedEntries.filter((entry) => {
            const [, , , , requiredPermission] = entry;
            return !requiredPermission || this.hasPermission(requiredPermission);
        });

        if (filteredPinned.length === 0) return nothing;

        return html`<ak-sidebar-item label=${msg("Pinned")} ?expanded=${true}>
            ${filteredPinned.map((entry) => this.renderSidebarEntry(entry))}
        </ak-sidebar-item>`;
    }

    /**
     * Render the main sidebar entries with permission filtering and pin support.
     * Excludes pinned entries from their original location (they appear in Pinned section).
     */
    private renderSidebarEntries(entries: readonly SidebarEntry[]): TemplateResult[] {
        return this.filterSidebarEntries(entries, true).map((entry) =>
            this.renderSidebarEntry(entry),
        );
    }

    render(): TemplateResult {
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
            <ak-page-navbar ?open=${this.sidebarOpen}>
                <ak-version-banner></ak-version-banner>
                <ak-enterprise-status interface="admin"></ak-enterprise-status>
            </ak-page-navbar>

            <ak-sidebar ?hidden=${!this.sidebarOpen} class="${classMap(sidebarClasses)}"
                >${this.renderPinnedSection()}
                ${this.renderSidebarEntries(createAdminSidebarEntries())}
                ${this.can(CapabilitiesEnum.IsEnterprise)
                    ? this.renderSidebarEntries(createAdminSidebarEnterpriseEntries())
                    : nothing}
            </ak-sidebar>

            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${classMap(drawerClasses)}">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <ak-admin-router-outlet
                                    role="presentation"
                                    class="pf-c-page__main"
                                    tabindex="-1"
                                    id="main-content"
                                    defaultUrl="/administration/overview"
                                    .routes=${ROUTES}
                                >
                                </ak-admin-router-outlet>
                            </div>
                        </div>
                        ${renderNotificationDrawerPanel(this.drawer)}
                        <ak-about-modal></ak-about-modal>
                    </div>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-admin": AdminInterface;
    }
}
