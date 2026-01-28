import "#components/ak-nav-buttons";
import "#elements/banner/EnterpriseStatusBanner";
import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/messages/MessageContainer";
import "#elements/notifications/APIDrawer";
import "#elements/notifications/NotificationDrawer";
import "#elements/router/RouterOutlet";
import "#elements/sidebar/Sidebar";
import "#elements/sidebar/SidebarItem";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { globalAK } from "#common/global";
import { configureSentry } from "#common/sentry/index";
import { isGuest } from "#common/users";
import { WebsocketClient } from "#common/ws/WebSocketClient";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { listen } from "#elements/decorators/listen";
import { WithBrandConfig } from "#elements/mixins/branding";
import { canAccessAdmin, WithSession } from "#elements/mixins/session";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import {
    DrawerState,
    persistDrawerParams,
    readDrawerParams,
    renderNotificationDrawerPanel,
} from "#elements/notifications/utils";
import { ifPresent } from "#elements/utils/attributes";
import { ThemedImage } from "#elements/utils/images";

import Styles from "#user/index.entrypoint.css";
import { ROUTES } from "#user/Routes";

import { ConsoleLogger } from "#logger/browser";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

@customElement("ak-interface-user")
class UserInterface extends WithBrandConfig(WithSession(AuthenticatedInterface)) {
    public static readonly styles = [
        PFDisplay,
        PFBrand,
        PFPage,
        PFAvatar,
        PFButton,
        PFDrawer,
        PFDropdown,
        PFNotificationBadge,
        Styles,
    ];

    #logger = ConsoleLogger.prefix("user-interface");

    @property({ attribute: false, useDefault: true })
    public drawer: DrawerState = readDrawerParams();

    @listen(AKDrawerChangeEvent)
    protected drawerListener = (event: AKDrawerChangeEvent) => {
        this.drawer = event.drawer;
        persistDrawerParams(event.drawer);
    };

    //#region Lifecycle

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();

        WebsocketClient.close();
    }

    //#endregion

    //#region Rendering

    protected renderAdminInterfaceLink() {
        return guard([this.currentUser], () => {
            if (!canAccessAdmin(this.currentUser)) {
                return nothing;
            }

            const { base } = globalAK().api;

            return html`<a
                    class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                    href="${base}if/admin/"
                    slot="extra"
                >
                    ${msg("Admin interface")}
                </a>
                <a
                    class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none-on-md pf-u-display-block"
                    href="${base}if/admin/"
                    slot="extra"
                >
                    ${msg("Admin")}
                </a>`;
        });
    }

    protected render() {
        const { currentUser } = this;

        const guest = isGuest(currentUser);

        if (!currentUser || guest) {
            this.#logger.debug("Waiting for user session", {
                currentUser,
                guest,
            });

            // TODO: There might be a hidden feature here.
            // Allowing guest users to see some parts of the interface?
            // Maybe redirect to a flow?
            return html`<slot name="placeholder"></slot>`;
        }

        const backgroundStyles = this.uiConfig.theme.background;

        return html`<ak-enterprise-status interface="user"></ak-enterprise-status>
            <div part="page" class="pf-c-page">
                <div part="background-wrapper" style=${ifPresent(backgroundStyles)}>
                    ${!backgroundStyles
                        ? html`<div part="background-default-slant"></div>`
                        : nothing}
                </div>
                <header part="page__header" class="pf-c-page__header">
                    <div part="brand" class="pf-c-page__header-brand">
                        <a href="#/" class="pf-c-page__header-brand-link">
                            ${ThemedImage({
                                src: this.brandingLogo,
                                alt: this.brandingTitle,
                                className: "pf-c-brand",
                                theme: this.activeTheme,
                            })}
                        </a>
                    </div>
                    <ak-nav-buttons>${this.renderAdminInterfaceLink()}</ak-nav-buttons>
                </header>
                <div class="pf-c-page__drawer">
                    <div
                        class="pf-c-drawer ${this.drawer.notifications || this.drawer.api
                            ? "pf-m-expanded"
                            : "pf-m-collapsed"}"
                    >
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <ak-router-outlet
                                        class="pf-l-bullseye__item pf-c-page__main"
                                        tabindex="-1"
                                        id="main-content"
                                        defaultUrl="/library"
                                        .routes=${ROUTES}
                                    >
                                    </ak-router-outlet>
                                </div>
                            </div>
                            ${renderNotificationDrawerPanel(this.drawer)}
                        </div>
                    </div>
                </div>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-user": UserInterface;
    }
}
