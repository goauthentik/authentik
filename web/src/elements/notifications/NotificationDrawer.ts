import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { EventsApi, Notification } from "authentik-api";
import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import { EVENT_NOTIFICATION_TOGGLE } from "../../constants";

@customElement("ak-notification-drawer")
export class NotificationDrawer extends LitElement {

    @property({attribute: false})
    notifications?: AKResponse<Notification>;

    @property({type: Number})
    unread = 0;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFNotificationDrawer, PFContent, PFDropdown, AKGlobal].concat(
            css`
                .pf-c-notification-drawer__list-item-description {
                    white-space: pre-wrap;
                }
            `
        );
    }

    firstUpdated(): void {
        new EventsApi(DEFAULT_CONFIG).eventsNotificationsList({
            seen: false,
            ordering: "-created",
        }).then(r => {
            this.notifications = r;
            this.unread = r.results.length;
        });
    }

    renderItem(item: Notification): TemplateResult {
        let level = "";
        switch (item.severity) {
        case "notice":
            level = "pf-m-info";
            break;
        case "warning":
            level = "pf-m-warning";
            break;
        case "alert":
            level = "pf-m-danger";
            break;
        default:
            break;
        }
        return html`<li class="pf-c-notification-drawer__list-item pf-m-read">
            <div class="pf-c-notification-drawer__list-item-header">
                <span class="pf-c-notification-drawer__list-item-header-icon ${level}">
                    <i class="fas fa-info-circle" aria-hidden="true"></i>
                </span>
                <h2 class="pf-c-notification-drawer__list-item-header-title">
                    ${item.event?.action}
                </h2>
            </div>
            <div class="pf-c-notification-drawer__list-item-action">
                ${item.event && html`
                    <a class="pf-c-dropdown__toggle pf-m-plain" href="#/events/log/${item.event?.pk}">
                        <i class="fas fas fa-share-square"></i>
                    </a>
                `}
                <button class="pf-c-dropdown__toggle pf-m-plain" type="button" @click=${() => {
                    new EventsApi(DEFAULT_CONFIG).eventsNotificationsPartialUpdate({
                        uuid: item.pk || "",
                        patchedNotificationRequest: {
                            seen: true,
                        }
                    }).then(() => {
                        this.firstUpdated();
                    });
                }}>
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <p class="pf-c-notification-drawer__list-item-description">${item.body}</p>
            <small class="pf-c-notification-drawer__list-item-timestamp">${item.created?.toLocaleString()}</small>
        </li>`;
    }

    render(): TemplateResult {
        if (!this.notifications) {
            return html``;
        }
        return html`<div class="pf-c-drawer__body pf-m-no-padding">
            <div class="pf-c-notification-drawer">
                <div class="pf-c-notification-drawer__header">
                    <h1 class="pf-c-notification-drawer__header-title">
                        ${t`Notifications`}
                    </h1>
                    <span class="pf-c-notification-drawer__header-status">
                        ${t`${this.unread} unread`}
                    </span>
                    <div class="pf-c-notification-drawer__header-action">
                        <div class="pf-c-notification-drawer__header-action-close">
                            <button
                                @click=${() => {
                                    this.dispatchEvent(
                                        new CustomEvent(EVENT_NOTIFICATION_TOGGLE, {
                                            bubbles: true,
                                            composed: true,
                                        })
                                    );
                                }}
                                class="pf-c-button pf-m-plain"
                                type="button"
                                aria-label="Close">
                                <i class="fas fa-times" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-notification-drawer__body">
                    <ul class="pf-c-notification-drawer__list">
                        ${this.notifications.results.map(n => this.renderItem(n))}
                    </ul>
                </div>
            </div>
        </div>`;
    }

}
