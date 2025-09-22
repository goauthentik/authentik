import "#components/ak-nav-buttons";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import styles from "./ak-page-navbar.css";
import { PageDetailsUpdate, PageNavMenuToggle } from "./ak-page-navbar.events";
import template from "./ak-page-navbar.template";
import type { PageHeaderInit } from "./ak-page-navbar.types";

import { EVENT_WS_MESSAGE } from "#common/constants";
import { globalAK } from "#common/global";
import { getConfigForUser, UIConfig, UserDisplay } from "#common/ui/config";
import { me } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { isAdminRoute } from "#elements/router/utils";
import { themeImage } from "#elements/utils/images";

import { SessionUser } from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { property, state } from "lit/decorators.js";

/**
 * A global navbar component at the top of the page.
 *
 * Internally, this component listens for the `ak-page-header` event, which is
 * dispatched by the `ak-page-header` component.
 */
export class AKPageNavbar extends WithBrandConfig(AKElement) implements PageHeaderInit {
    //#region Static Properties

    static styles = [styles];

    //#endregion

    //#region Properties

    @state()
    icon?: string;

    @state()
    iconImage = false;

    @state()
    header?: string;

    @state()
    description?: string;

    @state()
    hasIcon = true;

    @property({ type: Boolean, reflect: true })
    public open?: boolean;

    @state()
    protected session?: SessionUser;

    @state()
    protected uiConfig!: UIConfig;

    //#endregion

    //#region Private Methods

    #setTitle(header?: string) {
        const title = this.brandingTitle;
        document.title = match([isAdminRoute(), Boolean(header)])
            .with([true, P.any], () => `${msg("Admin")} - ${title}`)
            .with([false, true], () => `${header} - ${title}`)
            .otherwise(() => title);
    }

    #toggleSidebar() {
        this.open = !this.open;
        this.dispatchEvent(new PageNavMenuToggle(!!this.open));
    }

    //#endregion

    //#region Event Handlers

    #onWebSocket = () => {
        this.firstUpdated();
    };

    #onPageDetails = (ev: PageDetailsUpdate) => {
        const { header, description, icon, iconImage } = ev.header;
        this.header = header;
        this.description = description;
        this.icon = icon;
        this.iconImage = iconImage || false;
        this.hasIcon = !!icon;
    };

    //#endregion

    //#region Lifecycle

    public connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener(EVENT_WS_MESSAGE, this.#onWebSocket);
        window.addEventListener(PageDetailsUpdate.eventName, this.#onPageDetails);
    }

    public disconnectedCallback(): void {
        window.removeEventListener(EVENT_WS_MESSAGE, this.#onWebSocket);
        window.removeEventListener(PageDetailsUpdate.eventName, this.#onPageDetails);
        super.disconnectedCallback();
    }

    public async firstUpdated() {
        this.session = await me();
        this.uiConfig = getConfigForUser(this.session.user);
        this.uiConfig.navbar.userDisplay = UserDisplay.none;
    }

    willUpdate() {
        // Always update title, even if there's no header value set,
        // as in that case we still need to return to the generic title
        this.#setTitle(this.header);
    }

    //#endregion

    //#region Render

    render() {
        return template({
            open: Boolean(this.open),
            logo: themeImage(this.brandingLogo),
            onClick: this.#toggleSidebar,
            title: this.header ?? "",
            description: this.description,
            base: globalAK().api.base,
            session: this.session,
            uiConfig: this.uiConfig,
            icon: this.icon,
            iconIsImage: this.iconImage,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-page-navbar": AKPageNavbar;
    }
}
