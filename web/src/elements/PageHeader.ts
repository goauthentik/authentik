import { DEFAULT_CONFIG, tenant } from "@goauthentik/web/api/Config";
import { currentInterface } from "@goauthentik/web/api/Sentry";
import { me } from "@goauthentik/web/api/Users";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
    EVENT_WS_MESSAGE,
    TITLE_DEFAULT,
} from "@goauthentik/web/constants";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventsApi } from "@goauthentik/api";

@customElement("ak-page-header")
export class PageHeader extends LitElement {
    @property()
    icon?: string;

    @property({ type: Boolean })
    iconImage = false;

    @property({ type: Boolean })
    hasNotifications = false;

    @property()
    set header(value: string) {
        tenant().then((tenant) => {
            const currentIf = currentInterface();
            let title = tenant.brandingTitle || TITLE_DEFAULT;
            if (currentIf === "admin") {
                title = `${t`Admin`} - ${title}`;
            }
            if (value !== "") {
                title = `${value} - ${title}`;
            }
            document.title = title;
        });
        this._header = value;
    }

    get header(): string {
        return this._header;
    }

    @property()
    description?: string;

    _header = "";

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFContent,
            AKGlobal,
            css`
                :host {
                    display: flex;
                    flex-direction: row;
                    min-height: 114px;
                }
                .pf-c-button.pf-m-plain {
                    background-color: var(--pf-c-page__main-section--m-light--BackgroundColor);
                    border-radius: 0px;
                }
                .pf-c-page__main-section {
                    flex-grow: 1;
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
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener(EVENT_WS_MESSAGE, () => {
            this.firstUpdated();
        });
    }

    firstUpdated(): void {
        me().then((user) => {
            new EventsApi(DEFAULT_CONFIG)
                .eventsNotificationsList({
                    seen: false,
                    ordering: "-created",
                    pageSize: 1,
                    user: user.user.pk,
                })
                .then((r) => {
                    this.hasNotifications = r.pagination.count > 0;
                });
        });
    }

    renderIcon(): TemplateResult {
        if (this.icon) {
            if (this.iconImage && !this.icon.startsWith("fa://")) {
                return html`<img class="pf-icon" src="${this.icon}" />&nbsp;`;
            }
            const icon = this.icon.replaceAll("fa://", "fa ");
            return html`<i class=${icon}></i>&nbsp;`;
        }
        return html``;
    }

    render(): TemplateResult {
        return html`<button
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
                        ${this.renderIcon()}
                        <slot name="header"> ${this.header} </slot>
                    </h1>
                    ${this.description ? html`<p>${this.description}</p>` : html``}
                </div>
            </section>
            <button
                class="notification-trigger pf-c-button pf-m-plain"
                @click=${() => {
                    this.dispatchEvent(
                        new CustomEvent(EVENT_API_DRAWER_TOGGLE, {
                            bubbles: true,
                            composed: true,
                        }),
                    );
                }}
            >
                <i class="fas fa-code"></i>
            </button>
            <button
                class="notification-trigger pf-c-button pf-m-plain ${this.hasNotifications
                    ? "has-notifications"
                    : ""}"
                @click=${() => {
                    this.dispatchEvent(
                        new CustomEvent(EVENT_NOTIFICATION_DRAWER_TOGGLE, {
                            bubbles: true,
                            composed: true,
                        }),
                    );
                }}
            >
                <i class="fas fa-bell"></i>
            </button> `;
    }
}
