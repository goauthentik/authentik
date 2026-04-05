import "#elements/timestamp/ak-timestamp";

import { AKRequestPostEvent, APIRequestInfo } from "#common/api/events";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { AKDrawerChangeEvent } from "#elements/notifications/events";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";

function renderItem(item: APIRequestInfo, idx: number): TemplateResult {
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
    public requests: APIRequestInfo[] = [];

    static styles: CSSResult[] = [
        PFNotificationDrawer,
        PFButton,
        PFContent,
        PFDropdown,
        css`
            .pf-c-drawer__body {
                height: 100%;
            }

            .pf-c-notification-drawer__header {
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
                overflow-x: auto;
            }
        `,
    ];

    @listen(AKRequestPostEvent)
    protected enqueueRequest = ({ requestInfo }: AKRequestPostEvent) => {
        this.requests.push(requestInfo);

        this.requests.sort((a, b) => a.time - b.time).reverse();
        if (this.requests.length > 50) {
            this.requests.shift();
        }

        this.requestUpdate();
    };

    render(): TemplateResult {
        return html`<aside
            class="pf-c-drawer__body pf-m-no-padding"
            aria-label=${msg("API drawer")}
        >
            <div class="pf-c-notification-drawer">
                <header class="pf-c-notification-drawer__header">
                    <div class="text">
                        <h2 class="pf-c-notification-drawer__header-title">
                            ${msg("API Requests")}
                        </h2>
                        <a href="${globalAK().api.base}api/v3/" target="_blank"
                            >${msg("Open API Browser")}</a
                        >
                    </div>
                    <div class="pf-c-notification-drawer__header-action">
                        <div class="pf-c-notification-drawer__header-action-close">
                            <button
                                @click=${AKDrawerChangeEvent.dispatchAPIToggle}
                                class="pf-c-button pf-m-plain"
                                type="button"
                                aria-label=${msg("Close API drawer")}
                            >
                                <i class="fas fa-times" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </header>
                <div class="pf-c-notification-drawer__body">
                    <ul class="pf-c-notification-drawer__list">
                        ${this.requests.map(renderItem)}
                    </ul>
                </div>
            </div>
        </aside>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-api-drawer": APIDrawer;
    }
}
