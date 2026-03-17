import { WebsocketClient } from "#common/ws/WebSocketClient";

import type { Interface } from "#elements/Interface";

import { ReactiveController, ReactiveControllerHost } from "lit";

type WebsocketClientControllerHost = ReactiveControllerHost & Interface;

/**
 * Set up the web socket to listen for messages from the authentik server
 *
 * @remarks
 *
 * The authentik server may send notifications to the user's session. This controller handles the
 * lifecycle of our simple websocket listener, which filters and re-issues events into the DOM.
 * Users of this controller are expected to implement a listener and display the events to the user.
 * The current implementation uses `ak-message-notifications`, but that's just a detail.
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
