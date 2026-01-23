import "#components/ak-nav-buttons";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithSession } from "#elements/mixins/session";
import { isAdminRoute } from "#elements/router/utils";
import { ThemedImage } from "#elements/utils/images";

import Styles from "#components/ak-page-navbar.css";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

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
 *
 * @event ak-page-nav-menu-toggle
 * @event ak-page-details-update
 *
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
        Styles,
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

    //#endregion

    //#region Event Handlers

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
        window.addEventListener(PageDetailsUpdate.eventName, this.#onPageDetails);
    }

    public disconnectedCallback(): void {
        window.removeEventListener(PageDetailsUpdate.eventName, this.#onPageDetails);
        super.disconnectedCallback();
    }

    willUpdate() {
        // Always update title, even if there's no header value set,
        // as in that case we still need to return to the generic title
        this.#setTitle(this.header);
    }

    //#endregion

    //#region Render

    protected renderIcon() {
        return guard([this.icon, this.iconImage], () => {
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
        });
    }

    protected renderBrand() {
        return guard(
            [this.brandingLogo, this.activeTheme],
            () =>
                html`<aside role="presentation" class="brand">
                    <a aria-label="${msg("Home")}" href="#/">
                        <div class="logo">
                            ${ThemedImage({
                                src: this.brandingLogo,
                                alt: msg("authentik Logo"),
                                theme: this.activeTheme,
                            })}
                        </div>
                    </a>
                </aside>`,
        );
    }

    render(): TemplateResult {
        return html`<slot></slot>
            <div role="banner" aria-label="Main" class="main-content">
                ${this.renderBrand()}
                <slot name="toggle"></slot>

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
    }
}
