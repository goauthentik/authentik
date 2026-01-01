import { globalAK } from "#common/global";
import { createDebugLogger } from "#common/logger";
import { MessageLevel } from "#common/messages";
import { createEventFromWSMessage, WSMessage } from "#common/ws/events";

import { showMessage } from "#elements/messages/MessageContainer";

import { msg } from "@lit/localize";

/**
 * A websocket client that automatically reconnects.
 *
 * @singleton
 */
export class WebsocketClient extends WebSocket implements Disposable {
    static #debug = createDebugLogger("ws");
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
    #connectionTimeoutID = -1;

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

        const event = createEventFromWSMessage(data);

        if (event) {
            window.dispatchEvent(event);
        }
    };

    #openListener = () => {
        window.clearTimeout(this.#connectionTimeoutID);

        WebsocketClient.#debug(`connected to ${this.url}`);

        WebsocketClient.#connection = this;

        this.#retryDelay = 200;
    };

    #closeListener = (event: CloseEvent) => {
        window.clearTimeout(this.#connectionTimeoutID);

        console.debug("authentik/ws: closed ws connection", event);

        WebsocketClient.#connection = null;

        if (this.#retryDelay > 6000) {
            showMessage(
                {
                    level: MessageLevel.error,
                    message: msg("Connection error, reconnecting..."),
                },
                true,
            );
        }

        this.#connectionTimeoutID = window.setTimeout(() => {
            WebsocketClient.#debug(`reconnecting ws in ${this.#retryDelay}ms`);

            WebsocketClient.connect();
        }, this.#retryDelay);

        this.#retryDelay = this.#retryDelay * 2;
    };

    //#endregion
}
