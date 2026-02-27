/**
 * WebSocket event definitions.
 */

import { EVENT_REFRESH } from "#common/constants";
import { AKMessageEvent, APIMessage } from "#common/messages";

import { Notification, NotificationFromJSON } from "@goauthentik/api";

//#region WebSocket Messages

export enum WSMessageType {
    Message = "message",
    NotificationNew = "notification.new",
    Refresh = "refresh",
    SessionAuthenticated = "session.authenticated",
}

export interface WSMessageMessage extends APIMessage {
    message_type: WSMessageType.Message;
}

export interface WSMessageNotification {
    id: string;
    data: Notification;
    message_type: WSMessageType.NotificationNew;
}

export interface WSMessageRefresh {
    message_type: WSMessageType.Refresh;
}

export interface WSMessageSessionAuthenticated {
    message_type: WSMessageType.SessionAuthenticated;
}

export type WSMessage =
    | WSMessageMessage
    | WSMessageNotification
    | WSMessageRefresh
    | WSMessageSessionAuthenticated;

//#endregion

//#region WebSocket Events

export class AKNotificationEvent extends Event {
    static readonly eventName = "ak-notification";

    public readonly notification: Notification;

    constructor(input: Partial<Notification>) {
        super(AKNotificationEvent.eventName, { bubbles: true, composed: true });

        this.notification = NotificationFromJSON(input);
    }
}

export class AKSessionAuthenticatedEvent extends Event {
    static readonly eventName = "ak-session-authenticated";

    constructor() {
        super(AKSessionAuthenticatedEvent.eventName, { bubbles: true, composed: true });
    }
}

//#endregion

//#region Utilities

/**
 * Create an Event from a {@linkcode WSMessage}.
 *
 * @throws {TypeError} If the message type is unknown.
 */
export function createEventFromWSMessage(message: WSMessage): Event {
    switch (message.message_type) {
        case WSMessageType.Message:
            return new AKMessageEvent(message);
        case WSMessageType.NotificationNew:
            return new AKNotificationEvent(message.data);
        case WSMessageType.Refresh:
            return new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
            });
        case WSMessageType.SessionAuthenticated:
            return new AKSessionAuthenticatedEvent();
        default: {
            throw new TypeError(`Unknown WS message type: ${message satisfies never}`, {
                cause: message,
            });
        }
    }
}

declare global {
    interface WindowEventMap {
        [AKNotificationEvent.eventName]: AKNotificationEvent;
        [AKSessionAuthenticatedEvent.eventName]: AKSessionAuthenticatedEvent;
    }
}
