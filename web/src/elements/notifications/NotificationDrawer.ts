import "#elements/EmptyState";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { isAPIResultReady } from "#common/api/responses";
import { pluckErrorDetail } from "#common/errors/network";
import { globalAK } from "#common/global";
import { actionToLabel, severityToLevel } from "#common/labels";
import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { WithNotifications } from "#elements/mixins/notifications";
import { WithSession } from "#elements/mixins/session";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Notification } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { repeat } from "lit/directives/repeat.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";

@customElement("ak-notification-drawer")
export class NotificationDrawer extends WithNotifications(WithSession(AKElement)) {
    static styles: CSSResult[] = [
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

            .pf-c-notification-drawer__list-item-action {
                display: flex;
                flex-flow: row;
                align-items: start;
                gap: var(--pf-global--spacer--sm);
            }
        `,
    ];

    #APIBase = globalAK().api.base;

    //#region Rendering

    protected renderHyperlink(item: Notification) {
        if (!item.hyperlink) {
            return nothing;
        }

        return html`<small><a href=${item.hyperlink}>${item.hyperlinkLabel}</a></small>`;
    }

    #renderItem = (item: Notification): TemplateResult => {
        const label = actionToLabel(item.event?.action);
        const level = severityToLevel(item.severity);

        // There's little information we can have to determine if the body
        // contains code, but if it looks like JSON, we can at least style it better.
        const code = item.body.includes("{");

        return html`<li
            class="pf-c-notification-drawer__list-item"
            data-notification-action=${ifPresent(item.event?.action)}
        >
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
                        href="${this.#APIBase}if/admin/#/events/log/${item.event?.pk}"
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
                    @click=${() => this.markAsRead(item.pk)}
                    aria-label=${msg("Mark as read")}
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </div>
            ${code && item.event?.context
                ? html`<pre class="pf-c-notification-drawer__list-item-description">
${JSON.stringify(item.event.context, null, 2)}</pre
                  >`
                : html`<p class="pf-c-notification-drawer__list-item-description">${item.body}</p>`}
            <small class="pf-c-notification-drawer__list-item-timestamp"
                ><pf-tooltip position="top" .content=${item.created?.toLocaleString()}>
                    ${formatElapsedTime(item.created!)}
                </pf-tooltip></small
            >
            ${this.renderHyperlink(item)}
        </li>`;
    };

    protected renderEmpty() {
        return html`<ak-empty-state
            ><span>${msg("No notifications found.")}</span>
            <div slot="body">${msg("You don't have any notifications currently.")}</div>
        </ak-empty-state>`;
    }

    protected renderBody() {
        return guard([this.notifications], () => {
            if (this.notifications.loading) {
                return html`<ak-empty-state default-label></ak-empty-state>`;
            }

            if (this.notifications.error) {
                return html`<ak-empty-state icon="fa-ban"
                    ><span>${msg("Failed to fetch notifications.")}</span>
                    <div slot="body">${pluckErrorDetail(this.notifications.error)}</div>
                </ak-empty-state>`;
            }

            if (!this.notificationCount) {
                return this.renderEmpty();
            }

            return html`<ul class="pf-c-notification-drawer__list" role="list">
                ${repeat(
                    this.notifications.results,
                    (n) => n.pk,
                    (n) => this.#renderItem(n),
                )}
            </ul>`;
        });
    }

    protected override render(): SlottedTemplateResult {
        const unreadCount = isAPIResultReady(this.notifications) ? this.notificationCount : 0;

        return html`<aside
            class="pf-c-drawer__body pf-m-no-padding"
            aria-labelledby="notification-drawer-title"
        >
            <div class="pf-c-notification-drawer">
                <header class="pf-c-notification-drawer__header">
                    <div class="text">
                        <h2
                            id="notification-drawer-title"
                            class="pf-c-notification-drawer__header-title"
                        >
                            ${msg("Notifications")}
                        </h2>
                        <span aria-live="polite" aria-atomic="true">
                            ${msg(str`${unreadCount} unread`, {
                                id: "notification-unread-count",
                                desc: "Indicates the number of unread notifications in the notification drawer",
                            })}
                        </span>
                    </div>
                    <div class="pf-c-notification-drawer__header-action">
                        <button
                            @click=${this.clearNotifications}
                            class="pf-c-button pf-m-plain"
                            type="button"
                            aria-label=${msg("Clear all notifications", {
                                id: "notification-drawer-clear-all",
                            })}
                            ?disabled=${!unreadCount}
                        >
                            <i class="fa fa-trash" aria-hidden="true"></i>
                        </button>
                        <button
                            @click=${AKDrawerChangeEvent.dispatchNotificationsToggle}
                            class="pf-c-button pf-m-plain"
                            type="button"
                            aria-label=${msg("Close notification drawer", {
                                id: "notification-drawer-close",
                            })}
                        >
                            <i class="fas fa-times" aria-hidden="true"></i>
                        </button>
                    </div>
                </header>
                <div class="pf-c-notification-drawer__body">${this.renderBody()}</div>
            </div>
        </aside>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-notification-drawer": NotificationDrawer;
    }
}
