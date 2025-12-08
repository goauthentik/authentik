import "#elements/EmptyState";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_NOTIFICATION_DRAWER_TOGGLE, EVENT_REFRESH } from "#common/constants";
import { globalAK } from "#common/global";
import { actionToLabel, severityToLevel } from "#common/labels";
import { MessageLevel } from "#common/messages";
import { formatElapsedTime } from "#common/temporal";
import { isGuest } from "#common/users";

import { AKElement } from "#elements/Base";
import { showMessage } from "#elements/messages/MessageContainer";
import { WithSession } from "#elements/mixins/session";
import { PaginatedResponse } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { EventsApi, Notification } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-notification-drawer")
export class NotificationDrawer extends WithSession(AKElement) {
    @property({ attribute: false })
    notifications?: PaginatedResponse<Notification>;

    @property({ type: Number })
    unread = 0;

    static styles: CSSResult[] = [
        PFBase,
        PFButton,
        PFNotificationDrawer,
        PFContent,
        PFDropdown,
        css`
            .pf-c-drawer__body {
                height: 100%;
            }
            .pf-c-notification-drawer__body {
                flex-grow: 1;
                overflow-x: hidden;
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
    ];

    connectedCallback(): void {
        super.connectedCallback();
        this.refreshNotifications();
    }

    protected async refreshNotifications(): Promise<void> {
        const { currentUser } = this;

        if (!currentUser || isGuest(currentUser)) {
            return Promise.resolve();
        }

        return new EventsApi(DEFAULT_CONFIG)
            .eventsNotificationsList({
                seen: false,
                ordering: "-created",
                user: currentUser.pk,
            })
            .then((r) => {
                this.notifications = r;
                this.unread = r.results.length;
            });
    }

    protected renderHyperlink(item: Notification) {
        if (!item.hyperlink) {
          return nothing;
        }
        
        return html`<small><a href=${item.hyperlink}>${item.hyperlinkLabel}</a></small>`;
    }

    #renderItem = (item: Notification): TemplateResult => {
        const label = actionToLabel(item.event?.action);
        const level = severityToLevel(item.severity);

        return html`<li class="pf-c-notification-drawer__list-item">
            <div class="pf-c-notification-drawer__list-item-header">
                <span class="pf-c-notification-drawer__list-item-header-icon ${level}">
                    <i class="fas fa-info-circle" aria-hidden="true"></i>
                </span>
                <h2 class="pf-c-notification-drawer__list-item-header-title">${label}</h2>
            </div>
            <div class="pf-c-notification-drawer__list-item-action">
                ${item.event &&
                html`
                    <a
                        class="pf-c-dropdown__toggle pf-m-plain"
                        href="${globalAK().api.base}if/admin/#/events/log/${item.event?.pk}"
                        aria-label=${msg(str`View details for ${label}`)}
                    >
                        <pf-tooltip position="top" content=${msg("Show details")}>
                            <i class="fas fa-share-square" aria-hidden="true"></i>
                        </pf-tooltip>
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
                                this.refreshNotifications();
                                this.dispatchEvent(
                                    new CustomEvent(EVENT_REFRESH, {
                                        bubbles: true,
                                        composed: true,
                                    }),
                                );
                            });
                    }}
                    aria-label=${msg("Mark as read")}
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </div>
            <p class="pf-c-notification-drawer__list-item-description">${item.body}</p>
            <small class="pf-c-notification-drawer__list-item-timestamp"
                ><pf-tooltip position="top" .content=${item.created?.toLocaleString()}>
                    ${formatElapsedTime(item.created!)}
                </pf-tooltip></small
            >
            ${this.renderHyperlink(item)}
        </li>`;
    };

    clearNotifications() {
        new EventsApi(DEFAULT_CONFIG).eventsNotificationsMarkAllSeenCreate().then(() => {
            showMessage({
                level: MessageLevel.success,
                message: msg("Successfully cleared notifications"),
            });
            this.refreshNotifications();
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
    }

    renderEmpty() {
        return html`<ak-empty-state
            ><span>${msg("No notifications found.")}</span>
            <div slot="body">${msg("You don't have any notifications currently.")}</div>
        </ak-empty-state>`;
    }

    render(): SlottedTemplateResult {
        if (!this.notifications) {
            return nothing;
        }

        const { results } = this.notifications;

        return html`<div
            class="pf-c-drawer__body pf-m-no-padding"
            aria-label=${msg("Notification drawer")}
            role="region"
            tabindex="0"
        >
            <div class="pf-c-notification-drawer">
                <div class="pf-c-notification-drawer__header">
                    <div class="text">
                        <h1 class="pf-c-notification-drawer__header-title">
                            ${msg("Notifications")}
                        </h1>
                        <span> ${msg(str`${this.unread} unread`)}</span>
                    </div>
                    <div class="pf-c-notification-drawer__header-action">
                        <div>
                            <button
                                @click=${() => {
                                    this.clearNotifications();
                                }}
                                class="pf-c-button pf-m-plain"
                                type="button"
                                aria-label=${msg("Clear all")}
                            >
                                <i class="fa fa-trash" aria-hidden="true"></i>
                            </button>
                        </div>
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
                                aria-label=${msg("Close")}
                            >
                                <i class="fas fa-times" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-notification-drawer__body">
                    ${results.length
                        ? html`<ul class="pf-c-notification-drawer__list" role="list">
                              ${results.map((n) => this.#renderItem(n))}
                          </ul>`
                        : this.renderEmpty()}
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-notification-drawer": NotificationDrawer;
    }
}
