import { DEFAULT_CONFIG } from "#common/api/config";
import { APIResult, isAPIResultReady } from "#common/api/responses";
import { EVENT_NOTIFICATION_DRAWER_TOGGLE } from "#common/constants";
import { createDebugLogger } from "#common/logger";
import { MessageLevel } from "#common/messages";
import { isGuest } from "#common/users";

import { showMessage } from "#elements/messages/MessageContainer";
import { kAKSession, SessionContext } from "#elements/mixins/session";
import { createMixin } from "#elements/types";

import { EventsApi, type Notification, SessionUser } from "@goauthentik/api";

import { consume, createContext } from "@lit/context";
import { msg } from "@lit/localize";

export type NotificationsMap = Map<Notification["pk"], Notification>;
export const kAKNotifications = Symbol("kAKNotifications");

/**
 * The Lit context for the user's notifications.
 *
 * @category Context
 * @see {@linkcode SessionMixin}
 * @see {@linkcode WithSession}
 */
export const NotificationsContext = createContext<APIResult<NotificationsMap>>(
    Symbol.for("authentik-notifications-context"),
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
    readonly notifications: APIResult<Readonly<NotificationsMap>>;

    /**
     * Refresh the current user's notifications.
     *
     * @param requestInit Optional parameters to pass to the fetch call.
     */
    refreshNotifications(requestInit?: RequestInit): Promise<NotificationsMap>;

    /**
     * Mark a notification as read.
     *
     * @param notificationPk Primary key of the notification to mark as read.
     * @param requestInit Optional parameters to pass to the fetch call.
     */
    markAsRead(
        notificationPk: Notification["pk"],
        requestInit?: RequestInit,
    ): Promise<NotificationsMap>;

    /**
     * Clear all notifications.
     */
    clearNotifications(): Promise<void>;
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
            #log = createDebugLogger("notifications", this);
            #refreshAbortController: AbortController | null = null;

            @consume({
                context: SessionContext,
                subscribe,
            })
            public [kAKSession]!: APIResult<SessionUser>;

            // @consume({
            //     context: NotificationsContext,
            //     subscribe,
            // })
            // public notifications!: APIResult<Readonly<NotificationsMap>>;

            #data: APIResult<NotificationsMap> = {
                loading: true,
                error: null,
            };

            @consume({
                context: NotificationsContext,
                subscribe,
            })
            public set notifications(nextResult: APIResult<NotificationsMap>) {
                const previousValue = this.#data;

                this.#data = nextResult;

                this.requestUpdate("notifications", previousValue);
            }

            public get notifications(): APIResult<NotificationsMap> {
                return this.#data;
            }

            //#region Methods

            public refreshNotifications(requestInit?: RequestInit): Promise<NotificationsMap> {
                const session = this[kAKSession];

                console.log(">>> session in refreshNotifications", session);
                this.#refreshAbortController?.abort();

                if (!isAPIResultReady(session)) {
                    this.#log("Session not ready, skipping notifications refresh");
                    return Promise.resolve(new Map());
                }

                if (session.error) {
                    this.#log("Session error, skipping notifications refresh");
                    return Promise.resolve(new Map());
                }

                const currentNotifications = this.notifications;

                if (!session.user || isGuest(session.user)) {
                    this.#log("No current user, skipping");

                    this.notifications = new Map();
                    this.requestUpdate("notifications", currentNotifications);

                    return Promise.resolve(this.notifications);
                }

                this.#log("Fetching notifications...");

                this.#refreshAbortController = new AbortController();

                return new EventsApi(DEFAULT_CONFIG)
                    .eventsNotificationsList(
                        {
                            seen: false,
                            ordering: "-created",
                            user: session.user.pk,
                        },
                        {
                            signal: this.#refreshAbortController.signal,
                            ...requestInit,
                        },
                    )
                    .then((data) => {
                        this.notifications = new Map(
                            data.results.map((notification) => [notification.pk, notification]),
                        );

                        // this.requestUpdate("notifications", currentNotifications);

                        return this.notifications;
                    });
            }

            public markAsRead(
                notificationID: Notification["pk"],
                requestInit?: RequestInit,
            ): Promise<NotificationsMap> {
                this.#log(`Marking notification ${notificationID} as read...`);

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
            }

            public clearNotifications(): Promise<void> {
                return new EventsApi(DEFAULT_CONFIG)
                    .eventsNotificationsMarkAllSeenCreate()
                    .then(() => {
                        showMessage({
                            level: MessageLevel.success,
                            message: msg("Successfully cleared notifications"),
                        });

                        this.notifications = new Map();
                    })
                    .then(() => {
                        this.dispatchEvent(
                            new CustomEvent(EVENT_NOTIFICATION_DRAWER_TOGGLE, {
                                bubbles: true,
                                composed: true,
                            }),
                        );
                    });
            }
        }

        return NotificationsProvider;
    },
);
