import "#components/ak-nav-buttons";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { EVENT_WS_MESSAGE } from "#common/constants";
import { globalAK } from "#common/global";
import { UserDisplay } from "#common/ui/config";

import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithSession } from "#elements/mixins/session";
import { isAdminRoute } from "#elements/router/utils";
import { renderImage } from "#elements/utils/images";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

export class PageDetailsUpdate extends Event {
    static readonly eventName = "ak-page-details-update";
    header: PageHeaderInit;

    constructor(header: PageHeaderInit) {
        super(PageDetailsUpdate.eventName, { bubbles: true, composed: true });
        this.header = header;
    }
}

export class PageNavMenuToggle extends Event {
    static readonly eventName = "ak-page-nav-menu-toggle";
    open: boolean;

    constructor(open?: boolean) {
        super(PageNavMenuToggle.eventName, { bubbles: true, composed: true });
        this.open = !!open;
    }
}

export function setPageDetails(header: PageHeaderInit) {
    window.dispatchEvent(new PageDetailsUpdate(header));
}

export interface PageHeaderInit {
    header?: string | null;
    description?: string | null;
    icon?: string | null;
    iconImage?: boolean;
}

/**
 * A global navbar component at the top of the page.
 *
 * Internally, this component listens for the `ak-page-header` event, which is
 * dispatched by the `ak-page-header` component.
 */
@customElement("ak-page-navbar")
export class AKPageNavbar
    extends WithBrandConfig(WithSession(AKElement))
    implements PageHeaderInit
{
    //#region Static Properties

    static styles: CSSResult[] = [
        PFButton,
        PFPage,
        PFDrawer,

        PFNotificationBadge,
        PFContent,
        PFAvatar,
        PFDropdown,
        css`
            :host {
                position: sticky;
                top: 0;
                z-index: var(--pf-c-page__header--ZIndex);
                --pf-c-page__header-tools--MarginRight: 0;
                --ak-brand-logo-height: var(--pf-global--FontSize--4xl, 2.25rem);
                --ak-brand-background-color: var(--pf-c-page__sidebar--BackgroundColor);
                --host-navbar-height: var(--ak-c-page-header--height, 7.5rem);
            }

            :host([theme="dark"]) {
                --ak-brand-background-color: var(--pf-c-page__sidebar--BackgroundColor);

                .sidebar-trigger,
                .notification-trigger {
                    background-color: transparent !important;
                }
            }

            .main-content {
                border-bottom-width: 0.5px;
                border-bottom-style: solid;
                border-bottom-color: var(--pf-global--BorderColor--100);
                background-color: var(--pf-c-page__main-nav--BackgroundColor);
                display: flex;
                flex-direction: row;
                box-shadow: var(--pf-global--BoxShadow--sm-bottom);

                display: grid;
                column-gap: var(--pf-global--spacer--sm);
                grid-template-columns: [brand] auto [toggle] auto [primary] 1fr [secondary] auto;
                grid-template-rows: auto auto;
                grid-template-areas:
                    "brand toggle primary secondary"
                    "brand toggle description secondary";

                @media (min-width: 769px) {
                    height: var(--host-navbar-height);
                }

                @media (max-width: 768px) {
                    row-gap: var(--pf-global--spacer--xs);

                    align-items: center;
                    grid-template-areas:
                        "toggle primary secondary"
                        "toggle description description";
                    justify-content: space-between;
                    width: 100%;
                }
            }

            .items {
                display: block;

                &.primary {
                    grid-column: primary;
                    grid-row: primary / description;

                    align-self: center;
                    padding-block: var(--pf-global--spacer--md);

                    @media (max-width: 768px) {
                        padding-block: var(--pf-global--spacer--sm);
                    }

                    &.block-sibling {
                        align-self: end;
                    }

                    @media (min-width: 426px) {
                        &.block-sibling {
                            padding-block-end: 0;
                            grid-row: primary;
                        }
                    }

                    .accent-icon {
                        height: 1.2em;
                        width: 1em;

                        @media (max-width: 768px) {
                            display: none;
                        }
                    }
                }

                &.page-description {
                    padding-top: 0.3em;
                    grid-area: description;
                    margin-block-end: var(--pf-global--spacer--md);

                    display: box;
                    display: -webkit-box;
                    line-clamp: 2;
                    -webkit-line-clamp: 2;
                    box-orient: vertical;
                    -webkit-box-orient: vertical;
                    overflow: hidden;

                    @media (max-width: 425px) {
                        display: none;
                    }

                    @media (min-width: 769px) {
                        text-wrap: balance;
                    }
                }

                &.secondary {
                    grid-area: secondary;
                    flex: 0 0 auto;
                    justify-self: end;
                    padding-block: var(--pf-global--spacer--sm);
                    padding-inline-end: var(--pf-global--spacer--sm);

                    @media (min-width: 769px) {
                        align-content: center;
                        padding-block: var(--pf-global--spacer--md);
                        padding-inline-end: var(--pf-global--spacer--xl);
                    }
                }
            }

            .brand {
                grid-area: brand;
                background-color: var(--ak-brand-background-color);
                height: 100%;
                width: var(--pf-c-page__sidebar--Width);
                align-items: center;
                padding-inline: var(--pf-global--spacer--sm);

                display: flex;
                justify-content: center;

                &.pf-m-collapsed {
                    display: none;
                }

                @media (max-width: 1199px) {
                    display: none;
                }
            }

            .sidebar-trigger {
                grid-area: toggle;
                height: 100%;
            }

            .logo {
                flex: 0 0 auto;
                height: var(--ak-brand-logo-height);

                & img {
                    height: 100%;
                }

                & i {
                    font-size: var(--ak-brand-logo-height);
                    height: var(--ak-brand-logo-height);
                    line-height: var(--ak-brand-logo-height);
                }
            }

            .sidebar-trigger,
            .notification-trigger {
                font-size: 1.5rem;
            }

            .notification-trigger.has-notifications {
                color: var(--pf-global--active-color--100);
            }

            .pf-c-content .page-title {
                display: box;
                display: -webkit-box;
                line-clamp: 2;
                -webkit-line-clamp: 2;
                box-orient: vertical;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }

            h1 {
                display: flex;
                flex-direction: row;
                align-items: center !important;
            }
        `,
    ];

    //#endregion

    //#region Properties

    @state()
    icon?: string | null = null;

    @state()
    iconImage = false;

    @state()
    header?: string | null = null;

    @state()
    description?: string | null = null;

    @state()
    hasIcon = true;

    @property({ type: Boolean, reflect: true })
    public open?: boolean;

    //#endregion

    //#region Private Methods

    #setTitle(header?: string | null) {
        let title = this.brandingTitle;

        if (isAdminRoute()) {
            title = `${msg("Admin")} - ${title}`;
        }
        // Prepend the header to the title
        if (header) {
            title = `${header} - ${title}`;
        }
        document.title = title;
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
        this.uiConfig.navbar.userDisplay = UserDisplay.none;
    }

    willUpdate() {
        // Always update title, even if there's no header value set,
        // as in that case we still need to return to the generic title
        this.#setTitle(this.header);
    }

    //#endregion

    //#region Render

    renderIcon() {
        if (this.icon) {
            if (this.iconImage && !this.icon.startsWith("fa://")) {
                return html`<img
                    aria-hidden="true"
                    class="accent-icon pf-icon"
                    src="${this.icon}"
                    alt="page icon"
                />`;
            }

            const icon = this.icon.replaceAll("fa://", "fa ");

            return html`<i class="accent-icon ${icon}" aria-hidden="true"></i>`;
        }
        return nothing;
    }

    render(): TemplateResult {
        return html` <slot></slot>
            <div role="banner" aria-label="Main" class="main-content">
                <aside role="presentation" class="brand ${this.open ? "" : "pf-m-collapsed"}">
                    <a aria-label="${msg("Home")}" href="#/">
                        <div class="logo">
                            ${renderImage(this.brandingLogo, msg("authentik Logo"), "")}
                        </div>
                    </a>
                </aside>
                <button
                    aria-controls="global-nav"
                    class="sidebar-trigger pf-c-button pf-m-plain"
                    @click=${this.#toggleSidebar}
                    aria-label=${this.open ? msg("Collapse navigation") : msg("Expand navigation")}
                    aria-expanded=${this.open ? "true" : "false"}
                >
                    <i aria-hidden="true" class="fas fa-bars"></i>
                </button>

                <div class="items primary pf-c-content ${this.description ? "block-sibling" : ""}">
                    <h1 aria-labelledby="page-navbar-heading" class="page-title">
                        ${this.hasIcon
                            ? html`<slot aria-hidden="true" name="icon">${this.renderIcon()}</slot>`
                            : nothing}
                        <span id="page-navbar-heading">${this.header}</span>
                    </h1>
                </div>
                ${this.description
                    ? html`<div
                          role="heading"
                          aria-level="2"
                          aria-label="${this.description}"
                          class="items page-description pf-c-content"
                      >
                          <p>${this.description}</p>
                      </div>`
                    : nothing}

                <div class="items secondary">
                    <div class="pf-c-page__header-tools-group">
                        <ak-nav-buttons>
                            <a
                                class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                                href="${globalAK().api.base}if/user/"
                                slot="extra"
                            >
                                ${msg("User interface")}
                            </a>
                        </ak-nav-buttons>
                    </div>
                </div>
            </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-page-navbar": AKPageNavbar;
    }

    interface GlobalEventHandlersEventMap {
        [PageDetailsUpdate.eventName]: PageDetailsUpdate;
        [PageNavMenuToggle.eventName]: PageNavMenuToggle;
    }
}
