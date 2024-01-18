import { RequestInfo } from "@goauthentik/common/api/middleware";
import { EVENT_API_DRAWER_TOGGLE, EVENT_REQUEST_POST } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-api-drawer")
export class APIDrawer extends AKElement {
    @property({ attribute: false })
    requests: RequestInfo[] = [];

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFNotificationDrawer,
            PFButton,
            PFContent,
            PFDropdown,
            css`
                .pf-c-notification-drawer__header {
                    height: 114px;
                    align-items: center;
                }
                .pf-c-notification-drawer__header-action,
                .pf-c-notification-drawer__header-action-close,
                .pf-c-notification-drawer__header-action-close > .pf-c-button.pf-m-plain {
                    height: 100%;
                }
                .pf-c-notification-drawer__list-item-description {
                    white-space: pre-wrap;
                    font-family: monospace;
                }
                .pf-c-notification-drawer__body {
                    overflow-x: hidden;
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener(EVENT_REQUEST_POST, ((e: CustomEvent<RequestInfo>) => {
            this.requests.splice(0, 0, e.detail);
            if (this.requests.length > 50) {
                this.requests.shift();
            }
            this.requestUpdate();
        }) as EventListener);
    }

    renderItem(item: RequestInfo): TemplateResult {
        return html`<li class="pf-c-notification-drawer__list-item pf-m-read">
            <div class="pf-c-notification-drawer__list-item-header">
                <h2 class="pf-c-notification-drawer__list-item-header-title">
                    ${item.method}: ${item.status}
                </h2>
            </div>
            <a
                class="pf-c-notification-drawer__list-item-description"
                target="_blank"
                href=${item.path}
                >${item.path}</a
            >
        </li>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-drawer__body pf-m-no-padding">
            <div class="pf-c-notification-drawer">
                <div class="pf-c-notification-drawer__header">
                    <div class="text">
                        <h1 class="pf-c-notification-drawer__header-title">
                            ${msg("API Requests")}
                        </h1>
                        <a href="/api/v3/" target="_blank">${msg("Open API Browser")}</a>
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
                                aria-label="Close"
                            >
                                <i class="fas fa-times" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-notification-drawer__body">
                    <ul class="pf-c-notification-drawer__list">
                        ${this.requests.map((n) => this.renderItem(n))}
                    </ul>
                </div>
            </div>
        </div>`;
    }
}
