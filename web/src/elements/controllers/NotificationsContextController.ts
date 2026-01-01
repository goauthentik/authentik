import { APIResult, isAPIResultReady } from "#common/api/responses";
import { createSyntheticGenericError } from "#common/errors/network";
import { actionToLabel } from "#common/labels";
import { MessageLevel } from "#common/messages";
import { isGuest } from "#common/users";
import { AKNotificationEvent } from "#common/ws/events";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { showMessage } from "#elements/messages/MessageContainer";
import {
    NotificationsContext,
    NotificationsMap,
    NotificationsMixin,
} from "#elements/mixins/notifications";
import { SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { ContextProvider } from "@lit/context";
import { msg } from "@lit/localize";
import { html, nothing } from "lit";

export class NotificationsContextController extends ReactiveContextController<
    APIResult<NotificationsMap>
> {
    protected static override logPrefix = "notifications";

    #host: ReactiveElementHost<SessionMixin & NotificationsMixin>;
    #context: ContextProvider<NotificationsContext>;

    constructor(
        host: ReactiveElementHost<SessionMixin & NotificationsMixin>,
        initialValue?: NotificationsMap,
    ) {
        super();

        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: NotificationsContext,
            initialValue: initialValue ?? { loading: true, error: null },
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        if (!this.#host.refreshNotifications) {
            // This situation is unlikely, but possible if a host reference becomes
            // stale or is misconfigured.

            this.debug(
                "No `refreshNotifications` method available, skipping session fetch. Check if the `SessionMixin` is applied correctly.",
            );

            const result: APIResult<NotificationsMap> = {
                loading: false,
                error: createSyntheticGenericError("No `refreshNotifications` method available"),
            };

            return Promise.resolve(result);
        }

        return this.#host.refreshNotifications(requestInit);
    }

    protected doRefresh(notifications: APIResult<NotificationsMap>) {
        this.#context.setValue(notifications);
        this.#context.updateObservers();
        this.#host.requestUpdate?.();
    }

    public override hostConnected() {
        window.addEventListener(AKNotificationEvent.eventName, this.#messageListener, {
            passive: true,
        });
    }

    public override hostDisconnected() {
        this.#context.clearCallbacks();

        window.removeEventListener(AKNotificationEvent.eventName, this.#messageListener);

        super.hostDisconnected();
    }

    public hostUpdate() {
        const { currentUser } = this.#host;

        if (
            currentUser &&
            !isGuest(currentUser) &&
            !isAPIResultReady(this.#context.value) &&
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

        const currentNotifications = this.#context.value;

        if (isAPIResultReady(currentNotifications)) {
            this.debug("Adding notification to context", notification);
            currentNotifications.set(notification.pk, notification);
            this.#context.setValue(currentNotifications);
            this.#context.updateObservers();
        } else if (currentNotifications.error) {
            this.debug("Current notifications context in error state, refreshing");
            this.refresh();
        }
    };
}
