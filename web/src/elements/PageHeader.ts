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
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SessionUser } from "@goauthentik/api";

@customElement("ak-page-header")
export class PageHeader extends WithBrandConfig(AKElement) {
    @property()
    icon?: string;

    @property({ type: Boolean })
    iconImage = false;

    @property()
    header = "";

    @property()
    description?: string;

    @property({ type: Boolean })
    hasIcon = true;

    @state()
    me?: SessionUser;

    @state()
    uiConfig!: UIConfig;

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
                }
                .bar {
                    border-bottom: var(--pf-global--BorderWidth--sm);
                    border-bottom-style: solid;
                    border-bottom-color: var(--pf-global--BorderColor--100);
                    display: flex;
                    flex-direction: row;
                    min-height: 114px;
                    max-height: 114px;
                    background-color: var(--pf-c-page--BackgroundColor);
                }
                .pf-c-page__main-section.pf-m-light {
                    background-color: transparent;
                }
                .pf-c-page__main-section {
                    flex-grow: 1;
                    flex-shrink: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                img.pf-icon {
                    max-height: 24px;
                }
                .sidebar-trigger,
                .notification-trigger {
                    font-size: 24px;
                }
                .notification-trigger.has-notifications {
                    color: var(--pf-global--active-color--100);
                }
                h1 {
                    display: flex;
                    flex-direction: row;
                    align-items: center !important;
                }
                .pf-c-page__header-tools {
                    flex-shrink: 0;
                }
                .pf-c-page__header-tools-group {
                    height: 100%;
                }
                :host([theme="dark"]) .pf-c-page__header-tools {
                    color: var(--ak-dark-foreground) !important;
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener(EVENT_WS_MESSAGE, () => {
            this.firstUpdated();
        });
    }

    async firstUpdated() {
        this.me = await me();
        this.uiConfig = await uiConfig();
        this.uiConfig.navbar.userDisplay = UserDisplay.none;
    }

    setTitle(header?: string) {
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
        this.setTitle(this.header);
    }

    renderIcon() {
        if (this.icon) {
            if (this.iconImage && !this.icon.startsWith("fa://")) {
                return html`<img class="pf-icon" src="${this.icon}" alt="page icon" />`;
            }
            const icon = this.icon.replaceAll("fa://", "fa ");
            return html`<i class=${icon}></i>`;
        }
        return nothing;
    }

    render(): TemplateResult {
        return html`<div class="bar">
            <button
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
            <section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        ${this.hasIcon
                            ? html`<slot name="icon">${this.renderIcon()}</slot>&nbsp;`
                            : nothing}
                        <slot name="header">${this.header}</slot>
                    </h1>
                    ${this.description ? html`<p>${this.description}</p>` : html``}
                </div>
            </section>
            <div class="pf-c-page__header-tools">
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
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-page-header": PageHeader;
    }
}
