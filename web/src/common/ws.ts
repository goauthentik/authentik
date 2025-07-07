import { EVENT_MESSAGE, EVENT_WS_MESSAGE } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { MessageLevel } from "@goauthentik/common/messages";

import { msg } from "@lit/localize";

export interface WSMessage {
    message_type: string;
}

export class WebsocketClient extends WebSocket implements Disposable {
    #retryDelay = 200;

    constructor(url: string | URL) {
        super(url);

        this.addEventListener("open", this.#openListener);
        this.addEventListener("close", this.#closeListener);
        this.addEventListener("message", this.#messageListener);
        this.addEventListener("error", this.#errorListener);
    }

    public static connect(): WebsocketClient | null {
        if (navigator.webdriver) {
            return null;
        }

        const apiURL = new URL(globalAK().api.base);
        const wsURL = `${window.location.protocol.replace("http", "ws")}//${apiURL.host}${apiURL.pathname}ws/client/`;

        try {
            return new WebsocketClient(wsURL);
        } catch (error) {
            console.warn(`authentik/ws: failed to connect to ws ${error}`);
            return null;
        }
    }

    #errorListener = () => {
        this.#retryDelay = this.#retryDelay * 2;
    };

    #messageListener = (e: MessageEvent<string>) => {
        const data: WSMessage = JSON.parse(e.data);

        window.dispatchEvent(
            new CustomEvent(EVENT_WS_MESSAGE, {
                bubbles: true,
                composed: true,
                detail: data,
            }),
        );
    };

    #openListener = () => {
        console.debug(`authentik/ws: connected to ${this.url}`);

        this.#retryDelay = 200;
    };

    #closeListener = (e: CloseEvent) => {
        console.debug("authentik/ws: closed ws connection", e);

        if (this.#retryDelay > 6000) {
            window.dispatchEvent(
                new CustomEvent(EVENT_WS_MESSAGE, {
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
            console.debug(`authentik/ws: reconnecting ws in ${this.#retryDelay}ms`);
            WebsocketClient.connect();
        }, this.#retryDelay);

        this.#retryDelay = this.#retryDelay * 2;
    };

    public [Symbol.dispose]() {
        this.close();
    }
}
