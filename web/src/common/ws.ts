import { EVENT_MESSAGE, EVENT_WS_MESSAGE } from "#common/constants";
import { globalAK } from "#common/global";
import { MessageLevel } from "#common/messages";

import { msg } from "@lit/localize";

export interface WSMessage {
    message_type: string;
}

/**
 * A websocket client that automatically reconnects.
 *
 * @singleton
 */
export class WebsocketClient extends WebSocket implements Disposable {
    static #connection: WebsocketClient | null = null;

    public static get connection(): WebsocketClient | null {
        return WebsocketClient.#connection;
    }

    public static get connected(): boolean {
        return WebsocketClient.#connection?.readyState === WebSocket.OPEN;
    }

    public static get connecting(): boolean {
        return WebsocketClient.#connection?.readyState === WebSocket.CONNECTING;
    }

    public static close(): void {
        if (!WebsocketClient.#connection) {
            return;
        }

        if (WebsocketClient.#connection.readyState === WebSocket.CLOSED) {
            return;
        }

        return WebsocketClient.#connection.close();
    }

    public static [Symbol.dispose]() {
        return WebsocketClient.close();
    }

    #retryDelay = 200;

    //#endregion

    //#region Lifecycle

    constructor(url: string | URL) {
        super(url);

        this.addEventListener("open", this.#openListener);
        this.addEventListener("close", this.#closeListener);
        this.addEventListener("message", this.#messageListener);
        this.addEventListener("error", this.#errorListener);
    }

    public [Symbol.dispose]() {
        this.close();

        WebsocketClient.#connection = null;
    }

    public static connect(): WebsocketClient | null {
        if (navigator.webdriver) {
            return null;
        }

        WebsocketClient.#connection?.close();

        const apiURL = new URL(globalAK().api.base);
        const wsURL = `${window.location.protocol.replace("http", "ws")}//${apiURL.host}${apiURL.pathname}ws/client/`;

        try {
            return new WebsocketClient(wsURL);
        } catch (error) {
            console.warn(`authentik/ws: failed to connect to ws ${error}`);
            return null;
        }
    }

    //#endregion

    //#region Event listeners

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

        WebsocketClient.#connection = this;

        this.#retryDelay = 200;
    };

    #closeListener = (event: CloseEvent) => {
        console.debug("authentik/ws: closed ws connection", event);

        WebsocketClient.#connection = null;

        if (this.#retryDelay > 6000) {
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
            console.debug(`authentik/ws: reconnecting ws in ${this.#retryDelay}ms`);

            WebsocketClient.connect();
        }, this.#retryDelay);

        this.#retryDelay = this.#retryDelay * 2;
    };

    //#endregion
}
