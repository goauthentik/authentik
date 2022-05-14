import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventsApi, Notification } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { me } from "../../api/Users";
import { EVENT_NOTIFICATION_DRAWER_TOGGLE, EVENT_REFRESH } from "../../constants";
import { ActionToLabel } from "../../pages/events/utils";
import { MessageLevel } from "../messages/Message";
import { showMessage } from "../messages/MessageContainer";

@customElement("ak-notification-drawer")
export class NotificationDrawer extends LitElement {
    @property({ attribute: false })
    notifications?: AKResponse<Notification>;

    @property({ type: Number })
    unread = 0;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFNotificationDrawer, PFContent, PFDropdown, AKGlobal].concat(
            css`
                .pf-c-drawer__body {
                    height: 100%;
                }
                .pf-c-notification-drawer__body {
                    flex-grow: 1;
                }
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
                }
            `,
        );
    }

    firstUpdated(): void {
        me().then((user) => {
            new EventsApi(DEFAULT_CONFIG)
                .eventsNotificationsList({
                    seen: false,
                    ordering: "-created",
                    user: user.user.pk,
                })
                .then((r) => {
                    this.notifications = r;
                    this.unread = r.results.length;
                });
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
        return html`<li class="pf-c-notification-drawer__list-item">
            <div class="pf-c-notification-drawer__list-item-header">
                <span class="pf-c-notification-drawer__list-item-header-icon ${level}">
                    <i class="fas fa-info-circle" aria-hidden="true"></i>
                </span>
                <h2 class="pf-c-notification-drawer__list-item-header-title">
                    ${ActionToLabel(item.event?.action)}
                </h2>
            </div>
            <div class="pf-c-notification-drawer__list-item-action">
                ${item.event &&
                html`
                    <a
                        class="pf-c-dropdown__toggle pf-m-plain"
                        href="/if/admin/#/events/log/${item.event?.pk}"
                    >
                        <i class="fas fa-share-square"></i>
                    </a>
                `}
                <button
                    class="pf-c-dropdown__toggle pf-m-plain"
                    type="button"
                    @click=${() => {
                        new EventsApi(DEFAULT_CONFIG)
                            .eventsNotificationsPartialUpdate({
                                uuid: item.pk || "",
                                patchedNotificationRequest: {
                                    seen: true,
                                },
                            })
                            .then(() => {
                                this.firstUpdated();
                                this.dispatchEvent(
                                    new CustomEvent(EVENT_REFRESH, {
                                        bubbles: true,
                                        composed: true,
                                    }),
                                );
                            });
                    }}
                >
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <p class="pf-c-notification-drawer__list-item-description">${item.body}</p>
            <small class="pf-c-notification-drawer__list-item-timestamp"
                >${item.created?.toLocaleString()}</small
            >
        </li>`;
    }

    render(): TemplateResult {
        if (!this.notifications) {
            return html``;
        }
        return html`<div class="pf-c-drawer__body pf-m-no-padding">
            <div class="pf-c-notification-drawer">
                <div class="pf-c-notification-drawer__header">
                    <div class="text">
                        <h1 class="pf-c-notification-drawer__header-title">${t`Notifications`}</h1>
                        <span> ${t`${this.unread} unread`} </span>
                    </div>
                    <div class="pf-c-notification-drawer__header-action">
                        <div class="pf-c-notification-drawer__header-action-close">
                            <button
                                @click=${() => {
                                    this.dispatchEvent(
                                        new CustomEvent(EVENT_NOTIFICATION_DRAWER_TOGGLE, {
                                            bubbles: true,
                                            composed: true,
                                        }),
                                    );
                                }}
                                class="pf-c-button pf-m-plain"
                                type="button"
                                aria-label=${t`Close`}
                            >
                                <i class="fas fa-times" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-notification-drawer__body">
                    <ul class="pf-c-notification-drawer__list">
                        ${this.notifications.results.map((n) => this.renderItem(n))}
                    </ul>
                </div>
                <div class="pf-c-notification-drawer__footer">
                    <button
                        @click=${() => {
                            new EventsApi(DEFAULT_CONFIG)
                                .eventsNotificationsMarkAllSeenCreate()
                                .then(() => {
                                    showMessage({
                                        level: MessageLevel.success,
                                        message: t`Successfully cleared notifications`,
                                    });
                                    this.firstUpdated();
                                    this.dispatchEvent(
                                        new CustomEvent(EVENT_REFRESH, {
                                            bubbles: true,
                                            composed: true,
                                        }),
                                    );
                                    this.dispatchEvent(
                                        new CustomEvent(EVENT_NOTIFICATION_DRAWER_TOGGLE, {
                                            bubbles: true,
                                            composed: true,
                                        }),
                                    );
                                });
                        }}
                        class="pf-c-button pf-m-primary pf-m-block"
                        type="button"
                        aria-label=${t`Clear all`}
                    >
                        ${t`Clear all`}
                    </button>
                </div>
            </div>
        </div>`;
    }
}
