import { Middleware, ResponseContext } from "authentik-api";
import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import AKGlobal from "../../authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import { gettext } from "django";
import { EVENT_API_DRAWER_REFRESH } from "../../constants";

export interface RequestInfo {
    method: string;
    path: string;
}

export class APIMiddleware implements Middleware {
    requests: RequestInfo[];

    constructor() {
        this.requests = [];
    }

    post?(context: ResponseContext): Promise<Response | void> {
        this.requests.push({
            method: (context.init.method || "GET").toUpperCase(),
            path: context.url,
        });
        if (this.requests.length > MAX_REQUESTS) {
            this.requests.shift();
        }
        window.dispatchEvent(
            new CustomEvent(EVENT_API_DRAWER_REFRESH, {
                bubbles: true,
                composed: true,
            })
        );
        return Promise.resolve(context.response);
    }
}

export const MAX_REQUESTS = 50;
export const MIDDLEWARE = new APIMiddleware();

@customElement("ak-api-drawer")
export class APIDrawer extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFNotificationDrawer, PFContent, PFDropdown, AKGlobal];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_API_DRAWER_REFRESH, () => {
            this.requestUpdate();
        });
    }

    renderItem(item: RequestInfo): TemplateResult {
        return html`<li class="pf-c-notification-drawer__list-item pf-m-read">
            <div class="pf-c-notification-drawer__list-item-header">
                <h2 class="pf-c-notification-drawer__list-item-header-title">
                    ${item.method}
                </h2>
            </div>
            <p class="pf-c-notification-drawer__list-item-description">${item.path}</p>
        </li>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-drawer__body pf-m-no-padding">
            <div class="pf-c-notification-drawer">
                <div class="pf-c-notification-drawer__header pf-c-content">
                    <h1>
                        ${gettext("API Requests")}
                    </h1>
                </div>
                <div class="pf-c-notification-drawer__body">
                    <ul class="pf-c-notification-drawer__list">
                        ${MIDDLEWARE.requests.map(n => this.renderItem(n))}
                    </ul>
                </div>
            </div>
        </div>`;
    }

}
