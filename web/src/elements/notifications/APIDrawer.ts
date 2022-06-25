import { EVENT_API_DRAWER_REFRESH, EVENT_API_DRAWER_TOGGLE } from "@goauthentik/web/constants";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Middleware, ResponseContext } from "@goauthentik/api";

export interface RequestInfo {
    method: string;
    path: string;
    status: number;
}

export class APIMiddleware implements Middleware {
    post?(context: ResponseContext): Promise<Response | void> {
        const request: RequestInfo = {
            method: (context.init.method || "GET").toUpperCase(),
            path: context.url,
            status: context.response.status,
        };
        window.dispatchEvent(
            new CustomEvent(EVENT_API_DRAWER_REFRESH, {
                bubbles: true,
                composed: true,
                detail: request,
            }),
        );
        return Promise.resolve(context.response);
    }
}

@customElement("ak-api-drawer")
export class APIDrawer extends LitElement {
    @property({ attribute: false })
    requests: RequestInfo[] = [];

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFNotificationDrawer,
            PFButton,
            PFContent,
            PFDropdown,
            AKGlobal,
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
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener(EVENT_API_DRAWER_REFRESH, ((e: CustomEvent<RequestInfo>) => {
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
                        <h1 class="pf-c-notification-drawer__header-title">${t`API Requests`}</h1>
                        <a href="/api/v3/" target="_blank">${t`Open API Browser`}</a>
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
