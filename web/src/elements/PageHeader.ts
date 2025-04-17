import {
    EVENT_SIDEBAR_TOGGLE,
    EVENT_WS_MESSAGE,
    TITLE_DEFAULT,
} from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { currentInterface } from "@goauthentik/common/sentry";
import { UIConfig, UserDisplay, uiConfig } from "@goauthentik/common/ui/config";
import { me } from "@goauthentik/common/users";
import "@goauthentik/components/ak-nav-buttons";
import { AKElement } from "@goauthentik/elements/Base";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";
import { DefaultBrand } from "@goauthentik/elements/sidebar/SidebarBrand";
import { themeImage } from "@goauthentik/elements/utils/images";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, LitElement, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SessionUser } from "@goauthentik/api";

//#region Page Navbar

export interface PageNavbarDetails {
    header?: string;
    description?: string;
    icon?: string;
    iconImage?: boolean;
}

/**
 * A global navbar component at the top of the page.
 *
 * Internally, this component listens for the `ak-page-header` event, which is
 * dispatched by the `ak-page-header` component.
 */
@customElement("ak-page-navbar")
export class AKPageNavbar extends WithBrandConfig(AKElement) implements PageNavbarDetails {
    //#region Static Properties

    private static elementRef: AKPageNavbar | null = null;

    static readonly setNavbarDetails = (detail: Partial<PageNavbarDetails>): void => {
        const { elementRef } = AKPageNavbar;
        if (!elementRef) {
            console.debug(
                `ak-page-header: Could not find ak-page-navbar, skipping event dispatch.`,
            );
            return;
        }

        const { header, description, icon, iconImage } = detail;

        elementRef.header = header;
        elementRef.description = description;
        elementRef.icon = icon;
        elementRef.iconImage = iconImage || false;
        elementRef.hasIcon = !!icon;
    };

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFNotificationBadge,
            PFContent,
            PFAvatar,
            PFDropdown,
            css`
                :host {
                    position: sticky;
                    top: 0;
                    z-index: var(--pf-global--ZIndex--lg);
                    --pf-c-page__header-tools--MarginRight: 0;
                    --ak-brand-logo-height: var(--pf-global--FontSize--4xl, 2.25rem);

                    @media (prefers-color-scheme: dark) {
                        color: var(--ak-dark-foreground);
                    }
                }

                navbar {
                    border-bottom: var(--pf-global--BorderWidth--sm);
                    border-bottom-style: solid;
                    border-bottom-color: var(--pf-global--BorderColor--100);
                    background-color: var(--pf-c-page--BackgroundColor);

                    display: flex;
                    flex-direction: row;
                    min-height: 9rem;

                    padding-inline-end: var(--pf-global--spacer--xl);
                    display: grid;
                    grid-template-columns: auto 1fr auto;
                    justify-content: space-between;
                    gap: var(--pf-global--spacer--lg);
                    align-items: center;
                    width: 100%;
                }

                .items {
                    display: block;

                    &.primary {
                        padding-block: var(--pf-global--spacer--lg);

                        .accent-icon {
                            height: 1em;
                            width: 1em;
                        }
                    }

                    &.secondary {
                        padding-block: var(--pf-global--spacer--lg);
                        flex: 0 0 auto;
                        justify-self: end;
                    }
                }

                .logo {
                    flex: 0 0 auto;
                    height: var(--ak-brand-logo-height);

                    & img {
                        height: 100%;
                    }
                }

                .brand {
                    width: var(--pf-c-page__sidebar--Width);
                    padding-inline: var(--pf-global--spacer--sm);

                    display: flex;
                    justify-content: center;
                }

                @media (min-width: 1120px) {
                    .brand {
                        justify-content: center;
                    }
                }

                .sidebar-trigger,
                .notification-trigger {
                    font-size: 24px;
                }

                .notification-trigger.has-notifications {
                    color: var(--pf-global--active-color--100);
                }

                .page-title {
                    display: flex;
                    gap: var(--pf-global--spacer--sm);
                }

                h1 {
                    display: flex;
                    flex-direction: row;
                    align-items: center !important;
                }
            `,
        ];
    }

    //#endregion

    //#region Properties

    @property({ type: String })
    icon?: string;

    @property({ type: Boolean })
    iconImage = false;

    @property({ type: String })
    header?: string;

    @property({ type: String })
    description?: string;

    @property({ type: Boolean })
    hasIcon = true;

    @state()
    me?: SessionUser;

    @state()
    uiConfig!: UIConfig;

    //#endregion

    constructor() {
        super();
        window.addEventListener(EVENT_WS_MESSAGE, () => {
            this.firstUpdated();
        });
    }

    connectedCallback(): void {
        super.connectedCallback();
        AKPageNavbar.elementRef = this;
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        AKPageNavbar.elementRef = null;
    }

    public async firstUpdated() {
        this.me = await me();
        this.uiConfig = await uiConfig();
        this.uiConfig.navbar.userDisplay = UserDisplay.none;
    }

    #setTitle(header?: string) {
        const currentIf = currentInterface();
        let title = this.brand?.brandingTitle || TITLE_DEFAULT;
        if (currentIf === "admin") {
            title = `${msg("Admin")} - ${title}`;
        }
        // Prepend the header to the title
        if (header !== undefined && header !== "") {
            title = `${header} - ${title}`;
        }
        document.title = title;
    }

    willUpdate() {
        // Always update title, even if there's no header value set,
        // as in that case we still need to return to the generic title
        this.#setTitle(this.header);
    }

    //#region Render

    renderIcon() {
        if (this.icon) {
            if (this.iconImage && !this.icon.startsWith("fa://")) {
                return html`<img class="accent-icon pf-icon" src="${this.icon}" alt="page icon" />`;
            }

            const icon = this.icon.replaceAll("fa://", "fa ");

            return html`<i class="accent-icon ${icon}"></i>`;
        }
        return nothing;
    }

    render(): TemplateResult {
        return html`<navbar aria-label="Main" class="navbar">
            <aside class="brand">
                <button
                    style="display: none"
                    class="sidebar-trigger pf-c-button pf-m-plain"
                    @click=${() => {
                        this.dispatchEvent(
                            new CustomEvent(EVENT_SIDEBAR_TOGGLE, {
                                bubbles: true,
                                composed: true,
                            }),
                        );
                    }}
                >
                    <i class="fas fa-bars"></i>
                </button>

                <a href="#/">
                    <div class="logo">
                        <img
                            src=${themeImage(this.brand?.brandingLogo ?? DefaultBrand.brandingLogo)}
                            alt="${msg("authentik Logo")}"
                            loading="lazy"
                        />
                    </div>
                </a>
            </aside>

            <section class="items primary pf-c-content">
                <h1 class="page-title">
                    ${this.hasIcon ? html`<slot name="icon">${this.renderIcon()}</slot>` : nothing}
                    ${this.header}
                </h1>

                ${this.description ? html`<p>${this.description}</p>` : nothing}
            </section>

            <section class="items secondary">
                <div class="pf-c-page__header-tools-group">
                    <ak-nav-buttons .uiConfig=${this.uiConfig} .me=${this.me}>
                        <a
                            class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                            href="${globalAK().api.base}if/user/"
                            slot="extra"
                        >
                            ${msg("User interface")}
                        </a>
                    </ak-nav-buttons>
                </div>
            </section>
        </navbar>`;
    }

    //#endregion
}

//#endregion

//#region Page Header

/**
 * A page header component, used to display the page title and description.
 *
 * Internally, this component dispatches the `ak-page-header` event, which is
 * listened to by the `ak-page-navbar` component.
 *
 * @singleton
 */
@customElement("ak-page-header")
export class AKPageHeader extends LitElement implements PageNavbarDetails {
    @property({ type: String })
    header?: string;

    @property({ type: String })
    description?: string;

    @property({ type: String })
    icon?: string;

    @property({ type: Boolean })
    iconImage = false;

    static get styles(): CSSResult[] {
        return [
            css`
                :host {
                    display: none;
                }
            `,
        ];
    }

    connectedCallback(): void {
        super.connectedCallback();

        AKPageNavbar.setNavbarDetails({
            header: this.header,
            description: this.description,
            icon: this.icon,
            iconImage: this.iconImage,
        });
    }

    update(): void {
        AKPageNavbar.setNavbarDetails({
            header: this.header,
            description: this.description,
            icon: this.icon,
            iconImage: this.iconImage,
        });
    }
}

//#endregion

declare global {
    interface HTMLElementTagNameMap {
        "ak-page-header": AKPageHeader;
        "ak-page-navbar": AKPageNavbar;
    }
}
