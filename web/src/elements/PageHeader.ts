import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
    EVENT_WS_MESSAGE,
    TITLE_DEFAULT,
} from "@goauthentik/common/constants";
import { currentInterface } from "@goauthentik/common/sentry";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventsApi, SessionUser } from "@goauthentik/api";

@customElement("ak-page-header")
export class PageHeader extends WithBrandConfig(AKElement) {
    @property()
    icon?: string;

    @property({ type: Boolean })
    iconImage = false;

    @state()
    notificationsCount = 0;

    @property()
    header = "";

    @property()
    description?: string;

    @property({ type: Boolean })
    hasIcon = false;

    @state()
    me?: SessionUser;

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
                .bar {
                    border-bottom: var(--pf-global--BorderWidth--sm);
                    border-bottom-style: solid;
                    border-bottom-color: var(--pf-global--BorderColor--100);
                }
                .bar {
                    display: flex;
                    flex-direction: row;
                    min-height: 114px;
                    max-height: 114px;
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
        const notifications = await new EventsApi(DEFAULT_CONFIG).eventsNotificationsList({
            seen: false,
            ordering: "-created",
            pageSize: 1,
            user: this.me.user.pk,
        });
        this.notificationsCount = notifications.pagination.count;
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

    renderIcon(): TemplateResult {
        if (this.icon) {
            if (this.iconImage && !this.icon.startsWith("fa://")) {
                return html`<img class="pf-icon" src="${this.icon}" alt="page icon" />`;
            }
            const icon = this.icon.replaceAll("fa://", "fa ");
            return html`<i class=${icon}></i>`;
        }
        return html``;
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
                    <div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg">
                        <button
                            class="pf-c-button pf-m-plain"
                            type="button"
                            @click=${() => {
                                this.dispatchEvent(
                                    new CustomEvent(EVENT_API_DRAWER_TOGGLE, {
                                        bubbles: true,
                                        composed: true,
                                    }),
                                );
                            }}
                        >
                            <pf-tooltip position="top" content=${msg("Open API drawer")}>
                                <i class="fas fa-code" aria-hidden="true"></i>
                            </pf-tooltip>
                        </button>
                    </div>
                    <div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg">
                        <button
                            class="pf-c-button pf-m-plain"
                            type="button"
                            aria-label="${msg("Unread notifications")}"
                            @click=${() => {
                                this.dispatchEvent(
                                    new CustomEvent(EVENT_NOTIFICATION_DRAWER_TOGGLE, {
                                        bubbles: true,
                                        composed: true,
                                    }),
                                );
                            }}
                        >
                            <span
                                class="pf-c-notification-badge ${this.notificationsCount > 0
                                    ? "pf-m-unread"
                                    : ""}"
                            >
                                <pf-tooltip
                                    position="top"
                                    content=${msg("Open Notification drawer")}
                                >
                                    <i class="fas fa-bell" aria-hidden="true"></i>
                                </pf-tooltip>
                                <span class="pf-c-notification-badge__count"
                                    >${this.notificationsCount}</span
                                >
                            </span>
                        </button>
                    </div>
                    <div class="pf-c-page__header-tools-item">
                        <a class="pf-c-button pf-m-plain" type="button" href="/if/user/#/settings">
                            <pf-tooltip position="top" content=${msg("Settings")}>
                                <i class="fas fa-cog" aria-hidden="true"></i>
                            </pf-tooltip>
                        </a>
                    </div>
                    <div class="pf-c-page__header-tools-item">
                        <a href="/flows/-/default/invalidation/" class="pf-c-button pf-m-plain">
                            <pf-tooltip position="top" content=${msg("Sign out")}>
                                <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                            </pf-tooltip>
                        </a>
                    </div>
                    <img
                        class="pf-c-avatar"
                        src=${ifDefined(this.me?.user.avatar)}
                        alt="${msg("Avatar image")}"
                    />
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
