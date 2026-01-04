import { DEFAULT_CONFIG } from "#common/api/config";
import { isAPIResultReady } from "#common/api/responses";
import { actionToLabel } from "#common/labels";
import { MessageLevel } from "#common/messages";
import { isGuest } from "#common/users";
import { AKNotificationEvent } from "#common/ws/events";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { showMessage } from "#elements/messages/MessageContainer";
import {
    NotificationsContext,
    NotificationsContextValue,
    NotificationsMixin,
} from "#elements/mixins/notifications";
import { SessionMixin } from "#elements/mixins/session";
import { createPaginatedNotificationListFrom } from "#elements/notifications/utils";
import type { ReactiveElementHost } from "#elements/types";

import { EventsApi } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import { msg } from "@lit/localize";
import { html, nothing } from "lit";

export class NotificationsContextController extends ReactiveContextController<NotificationsContextValue> {
    protected static override logPrefix = "notifications";

    public host: ReactiveElementHost<SessionMixin & NotificationsMixin>;
    public context: ContextProvider<NotificationsContext>;

    constructor(host: ReactiveElementHost<SessionMixin & NotificationsMixin>) {
        super();

        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: NotificationsContext,
            initialValue: { loading: true, error: null },
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        const fallback = createPaginatedNotificationListFrom();

        const { session } = this.host;

        if (!isAPIResultReady(session)) {
            this.logger.info("Session not ready, skipping notifications refresh");
            return Promise.resolve(fallback);
        }

        if (session.error) {
            this.logger.warn("Session error, skipping notifications refresh");
            return Promise.resolve(fallback);
        }

        if (!session.user || isGuest(session.user)) {
            this.logger.info("No current user, skipping");

            return Promise.resolve(fallback);
        }

        this.logger.debug("Fetching notifications...");

        return new EventsApi(DEFAULT_CONFIG)
            .eventsNotificationsList(
                {
                    seen: false,
                    ordering: "-created",
                    user: session.user.pk,
                },
                {
                    ...requestInit,
                },
            )
            .then((data) => {
                this.host.notifications = data;

                return this.host.notifications;
            });
    }

    protected doRefresh(notifications: NotificationsContextValue) {
        this.context.setValue(notifications);
        this.host.requestUpdate?.();
    }

    public override hostConnected() {
        window.addEventListener(AKNotificationEvent.eventName, this.#messageListener, {
            passive: true,
        });
    }

    public override hostDisconnected() {
        window.removeEventListener(AKNotificationEvent.eventName, this.#messageListener);

        super.hostDisconnected();
    }

    public hostUpdate() {
        const { currentUser } = this.host;

        if (
            currentUser &&
            !isGuest(currentUser) &&
            !isAPIResultReady(this.host.notifications) &&
            !this.abortController
        ) {
            this.refresh();

            return;
        }

        if (!currentUser) {
            this.abort("Session Invalidated");
        }
    }

    #messageListener = ({ notification }: AKNotificationEvent) => {
        showMessage({
            level: MessageLevel.info,
            message: actionToLabel(notification.event?.action) ?? notification.body,
            description: html`${notification.body}
            ${notification.hyperlink
                ? html`<br /><a href=${notification.hyperlink}>${notification.hyperlinkLabel}</a>`
                : nothing}
            ${notification.event
                ? html`<br /><a href="#/events/log/${notification.event.pk}"
                          >${msg("View details...")}</a
                      >`
                : nothing}`,
        });

        const currentNotifications = this.context.value;

        if (isAPIResultReady(currentNotifications)) {
            this.logger.info("Adding notification to context");

            const appended = createPaginatedNotificationListFrom([
                notification,
                ...currentNotifications.results,
            ]);

            this.context.setValue(appended);

            this.host.requestUpdate?.();
        } else if (currentNotifications?.error) {
            this.logger.info("Current notifications context in error state, refreshing");
            this.refresh();
        }
    };
}
