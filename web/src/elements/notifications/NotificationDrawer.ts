import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { EventsApi, Notification } from "../../api";
import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-notification-drawer")
export class NotificationDrawer extends LitElement {

    @property({attribute: false})
    notifications?: AKResponse<Notification>;

    @property({type: Number})
    unread = 0;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                .pf-c-notification-drawer__header {
                    height: 114px;
                    padding: var(--pf-c-page__main-section--PaddingTop) var(--pf-c-page__main-section--PaddingRight) var(--pf-c-page__main-section--PaddingBottom) var(--pf-c-page__main-section--PaddingLeft);
                    display: flex;
                    flex-direction: column;
                }
                .pf-c-notification-drawer__list-item-description {
                    white-space: pre-wrap;
                }
            `
        );
    }

    firstUpdated(): void {
        new EventsApi(DEFAULT_CONFIG).eventsNotificationsList({
            seen: "false",
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
        return html`<li class="pf-c-notification-drawer__list-item pf-m-read ${level}">
            <div class="pf-c-notification-drawer__list-item-header">
                <span class="pf-c-notification-drawer__list-item-header-icon">
                    <i class="fas fa-info-circle" aria-hidden="true"></i>
                </span>
                <h2 class="pf-c-notification-drawer__list-item-header-title">
                    ${item.event?.action}
                </h2>
            </div>
            <div class="pf-c-notification-drawer__list-item-action">
                <button class="pf-c-dropdown__toggle pf-m-plain" type="button" @click=${() => {
                    new EventsApi(DEFAULT_CONFIG).eventsNotificationsPartialUpdate({
                        uuid: item.pk || "",
                        data: {
                            seen: true,
                        }
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
                <div class="pf-c-notification-drawer__header pf-c-content">
                    <h1>
                        ${gettext("Notifications")}
                    </h1>
                    <p>
                        ${gettext(`${this.unread} unread`)}
                    </p>
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
