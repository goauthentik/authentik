import { EVENT_MESSAGE, EVENT_WS_MESSAGE } from "@goauthentik/common/constants.js";
import { MessageLevel } from "@goauthentik/common/messages.js";

import { msg } from "@lit/localize";

export interface WSMessage {
    message_type: string;
}

const MESSAGE_RETRY_DELAY = 200; // milliseconds
const CLOSE_RETRY_DELAY = 6000; // milliseconds
const OPEN_RETRY_DELAY = 200; // milliseconds
const RETRY_BACKOFF = 2;

export class WebsocketClient {
    messageSocket?: WebSocket;
    retryDelay = MESSAGE_RETRY_DELAY;

    constructor() {
        try {
            this.connect();
        } catch (error) {
            console.warn(`authentik/ws: failed to connect to ws ${error}`);
        }
    }

    connect(): void {
        if (navigator.webdriver) {
            return;
        }
        const wsUrl = `${window.location.protocol.replace("http", "ws")}//${
            window.location.host
        }/ws/client/`;
        this.messageSocket = new WebSocket(wsUrl);
        this.messageSocket.addEventListener("open", () => {
            console.debug(`authentik/ws: connected to ${wsUrl}`);
            this.retryDelay = OPEN_RETRY_DELAY;
        });
        this.messageSocket.addEventListener("close", (e) => {
            console.debug("authentik/ws: closed ws connection", e);
            if (this.retryDelay > CLOSE_RETRY_DELAY) {
                window.dispatchEvent(
                    new CustomEvent(EVENT_MESSAGE, {
                        bubbles: true,
                        composed: true,
                        detail: {
                            level: MessageLevel.error,
                            message: msg("Connection error, reconnecting..."),
                        },
                    }),
                );
            }
            setTimeout(() => {
                console.debug(`authentik/ws: reconnecting ws in ${this.retryDelay}ms`);
                this.connect();
            }, this.retryDelay);
            this.retryDelay = this.retryDelay * RETRY_BACKOFF;
        });
        this.messageSocket.addEventListener("message", (e) => {
            const data = JSON.parse(e.data);
            window.dispatchEvent(
                new CustomEvent(EVENT_WS_MESSAGE, {
                    bubbles: true,
                    composed: true,
                    detail: data as WSMessage,
                }),
            );
        });
        this.messageSocket.addEventListener("error", () => {
            this.retryDelay = this.retryDelay * RETRY_BACKOFF;
        });
    }
}
