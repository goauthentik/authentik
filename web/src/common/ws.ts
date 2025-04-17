import { EVENT_MESSAGE, EVENT_WS_MESSAGE } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import { ServerContext } from "@goauthentik/common/server-context";

import { msg } from "@lit/localize";

export interface WSMessage {
    message_type: string;
}

export class WebsocketClient {
    messageSocket?: WebSocket;
    retryDelay = 200;

    constructor() {
        try {
            this.connect();
        } catch (error) {
            console.warn(`authentik/ws: failed to connect to ws ${error}`);
        }
    }

    connect(): void {
        if (navigator.webdriver) return;

        const apiURL = new URL(ServerContext.baseURL);

        const wsURL = `${window.location.protocol.replace("http", "ws")}//${apiURL.host}${apiURL.pathname}ws/client/`;

        this.messageSocket = new WebSocket(wsURL);
        this.messageSocket.addEventListener("open", () => {
            console.debug(`authentik/ws: connected to ${wsURL}`);
            this.retryDelay = 200;
        });
        this.messageSocket.addEventListener("close", (e) => {
            console.debug("authentik/ws: closed ws connection", e);
            if (this.retryDelay > 6000) {
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
            this.retryDelay = this.retryDelay * 2;
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
            this.retryDelay = this.retryDelay * 2;
        });
    }
}
