import { DEFAULT_CONFIG } from "#common/api/config";
import { APIResult, isAPIResultReady } from "#common/api/responses";
import { MessageLevel } from "#common/messages";

import { ContextControllerRegistry } from "#elements/controllers/ContextControllerRegistry";
import { showMessage } from "#elements/messages/MessageContainer";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import { createPaginatedNotificationListFrom } from "#elements/notifications/utils";
import { createMixin } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import {
    EventsApi,
    type Notification,
    PaginatedNotificationList,
    SessionUser,
} from "@goauthentik/api";

import { consume, createContext } from "@lit/context";
import { msg } from "@lit/localize";
import { property } from "lit/decorators.js";

export type NotificationsContextValue = APIResult<Readonly<PaginatedNotificationList>>;

/**
 * The Lit context for the user's notifications.
 *
 * @category Context
 * @see {@linkcode SessionMixin}
 * @see {@linkcode WithSession}
 */
export const NotificationsContext = createContext<NotificationsContextValue>(
    Symbol("authentik-notifications-context"),
);

export type NotificationsContext = typeof NotificationsContext;

/**
 * A mixin that provides the current version to the element.
 *
 * @see {@linkcode WithNotifications}
 */
export interface NotificationsMixin {
    /**
     * The current user's notifications.
     */
    readonly notifications: APIResult<Readonly<PaginatedNotificationList>>;

    /**
     * The total count of unread notifications, including those not loaded.
     */
    readonly notificationCount: number;
    /**
     * Refresh the current user's notifications.
     *
     * @param requestInit Optional parameters to pass to the fetch call.
     */
    refreshNotifications(): Promise<void>;

    /**
     * Mark a notification as read.
     *
     * @param notificationPk Primary key of the notification to mark as read.
     * @param requestInit Optional parameters to pass to the fetch call.
     */
    markAsRead: (notificationPk: Notification["pk"], requestInit?: RequestInit) => Promise<void>;

    /**
     * Clear all notifications.
     */
    clearNotifications: () => Promise<void>;
}

/**
 * A mixin that provides the current authentik version to the element.
 *
 * @category Mixin
 */
export const WithNotifications = createMixin<NotificationsMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class NotificationsProvider extends SuperClass implements NotificationsMixin {
            #logger = ConsoleLogger.prefix("notifications");
            #contextController = ContextControllerRegistry.get(NotificationsContext);

            public session!: APIResult<Readonly<SessionUser>>;

            public get notificationCount(): number {
                if (!isAPIResultReady(this.notifications)) {
                    return 0;
                }

                return this.notifications.pagination.count;
            }

            @consume({
                context: NotificationsContext,
                subscribe,
            })
            @property({ attribute: false })
            public notifications!: APIResult<Readonly<PaginatedNotificationList>>;

            //#region Methods

            public refreshNotifications = async (): Promise<void> => {
                await this.#contextController?.refresh();
            };

            public markAsRead = (
                notificationID: Notification["pk"],
                requestInit?: RequestInit,
            ): Promise<void> => {
                this.#logger.debug(`Marking notification ${notificationID} as read...`);

                return new EventsApi(DEFAULT_CONFIG)
                    .eventsNotificationsPartialUpdate(
                        {
                            uuid: notificationID || "",
                            patchedNotificationRequest: {
                                seen: true,
                            },
                        },
                        requestInit,
                    )
                    .then(() => this.refreshNotifications());
            };

            public clearNotifications = (): Promise<void> => {
                return new EventsApi(DEFAULT_CONFIG)
                    .eventsNotificationsMarkAllSeenCreate()
                    .then(() => {
                        showMessage({
                            level: MessageLevel.success,
                            message: msg("Successfully cleared notifications"),
                        });

                        this.#contextController?.context.setValue(
                            createPaginatedNotificationListFrom(),
                        );

                        this.requestUpdate?.();
                    })
                    .then(AKDrawerChangeEvent.dispatchCloseNotifications);
            };
        }

        return NotificationsProvider;
    },
);
