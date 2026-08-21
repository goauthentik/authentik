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

export type WSMessage = WSMessageMessage | WSMessageNotification | WSMessageRefresh;

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
    }
}
