import "#elements/timestamp/ak-timestamp";

import { RequestInfo } from "#common/api/middleware";
import { EVENT_API_DRAWER_TOGGLE, EVENT_REQUEST_POST } from "#common/constants";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";

function renderItem(item: RequestInfo, idx: number): TemplateResult {
    const subheading = `${item.method}: ${item.status}`;

    const label = URL.canParse(item.path) ? new URL(item.path).pathname : null;

    return html`<li
        class="pf-c-notification-drawer__list-item pf-m-read"
        aria-label=${label ?? subheading}
    >
        <div class="pf-c-notification-drawer__list-item-header">
            <h2
                class="pf-c-notification-drawer__list-item-header-title"
                id="notification-list-item-${idx}"
            >
                ${item.method}: ${item.status}
            </h2>
        </div>
        <a class="pf-c-notification-drawer__list-item-description" target="_blank" href=${item.path}
            >${label ?? item.path}</a
        >
        <div class="pf-c-notification-drawer__list-item-timestamp">
            <ak-timestamp .timestamp=${item.time} refresh datetime></ak-timestamp>
        </div>
    </li>`;
}

@customElement("ak-api-drawer")
export class APIDrawer extends AKElement {
    @property({ attribute: false })
    requests: RequestInfo[] = [];

    static styles: CSSResult[] = [
        PFNotificationDrawer,
        PFButton,
        PFContent,
        PFDropdown,
        css`
            :host {
                --header-height: 114px;
            }
            .pf-c-notification-drawer__header {
                height: var(--header-height);
                align-items: center;
            }
            .pf-c-notification-drawer__header-action,
            .pf-c-notification-drawer__header-action-close,
            .pf-c-notification-drawer__header-action-close > .pf-c-button.pf-m-plain {
                height: 100%;
            }
            .pf-c-notification-drawer__list-item-description {
                white-space: pre-wrap;
                font-family: var(--pf-global--FontFamily--monospace);
            }
            .pf-c-notification-drawer__body {
                overflow-x: hidden;
            }
            .pf-c-notification-drawer__list {
                max-height: calc(100vh - var(--header-height));
            }
        `,
    ];

    constructor() {
        super();
        window.addEventListener(EVENT_REQUEST_POST, ((e: CustomEvent<RequestInfo>) => {
            this.requests.push(e.detail);
            this.requests.sort((a, b) => a.time - b.time).reverse();
            if (this.requests.length > 50) {
                this.requests.shift();
            }
            this.requestUpdate();
        }) as EventListener);
    }

    render(): TemplateResult {
        return html`<div
            class="pf-c-drawer__body pf-m-no-padding"
            aria-label=${msg("API drawer")}
            role="region"
            tabindex="0"
        >
            <div class="pf-c-notification-drawer">
                <div class="pf-c-notification-drawer__header">
                    <div class="text">
                        <h1 class="pf-c-notification-drawer__header-title">
                            ${msg("API Requests")}
                        </h1>
                        <a href="${globalAK().api.base}api/v3/" target="_blank"
                            >${msg("Open API Browser")}</a
                        >
                    </div>
                    <div class="pf-c-notification-drawer__header-action">
                        <div class="pf-c-notification-drawer__header-action-close">
                            <button
                                @click=${() => {
                                    this.dispatchEvent(
                                        new CustomEvent(EVENT_API_DRAWER_TOGGLE, {
                                            bubbles: true,
                                            composed: true,
                                        }),
                                    );
                                }}
                                class="pf-c-button pf-m-plain"
                                type="button"
                                aria-label=${msg("Close API drawer")}
                            >
                                <i class="fas fa-times" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-notification-drawer__body">
                    <ul class="pf-c-notification-drawer__list">
                        ${this.requests.map(renderItem)}
                    </ul>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-api-drawer": APIDrawer;
    }
}
