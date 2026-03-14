import { WebsocketClient } from "#common/ws/WebSocketClient";

import type { Interface } from "#elements/Interface";

import { ReactiveController, ReactiveControllerHost } from "lit";

type WebsocketClientControllerHost = ReactiveControllerHost & Interface;

/**
 * Set up the web socket to listen for messages from the authentik server
 *
 * @remarks
 *
 * The authentik server may send notifications to the user's session. This controls the lifecycle of
 * a simple websocket listener. Events will be forwarded to the notification handler.
 *
 */
export class FlowWebsocketClientController implements ReactiveController {
    constructor(private host: WebsocketClientControllerHost) {
        /* no op */
    }

    hostConnected() {
        WebsocketClient.connect();
    }

    hostDisconnected() {
        WebsocketClient.close();
    }
}
