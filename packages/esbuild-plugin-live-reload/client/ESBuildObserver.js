/**
 * @file Client-side observer for ESBuild events.
 *
 * @import { Logger } from "@goauthentik/esbuild-plugin-live-reload/shared";
 * @import { Message as ESBuildMessage } from "esbuild";
 */

/// <reference types="./types.js" />

import { createLogger } from "@goauthentik/esbuild-plugin-live-reload/shared";

if (typeof EventSource === "undefined") {
    throw new TypeError("Environment doesn't appear to have an EventSource constructor");
}

/**
 * @template {unknown} [Data=unknown]
 * @typedef {(event: MessageEvent) => void} BuildEventListener
 */

/**
 * A client-side watcher for ESBuild.
 *
 * Note that this should be conditionally imported in your code, so that
 * ESBuild may tree-shake it out of production builds.
 *
 * ```ts
 * if (process.env.NODE_ENV === "development") {
 *   await import("@goauthentik/esbuild-plugin-live-reload/client")
 *     .catch(() => console.warn("Failed to import watcher"))
 * }
 * ```
 *
 * @implements {Disposable}
 * @category Plugin
 * runtime browser
 */
export class ESBuildObserver extends EventSource {
    /**
     * @type {Logger}
     */
    #logger;

    /**
     * Whether the watcher has a recent connection to the server.
     */
    alive = true;

    /**
     * The number of errors that have occurred since the watcher started.
     */
    errorCount = 0;

    /**
     * Whether a reload has been requested while offline.
     */
    deferredReload = false;

    /**
     * The last time a message was received from the server.
     */
    lastUpdatedAt = Date.now();

    /**
     * Whether the browser considers itself online.
     */
    online = true;

    /**
     * The ID of the animation frame for the reload.
     */
    #reloadFrameID = -1;

    /**
     * The interval for the keep-alive check.
     * @type {ReturnType<typeof setInterval> | undefined}
     */
    #keepAliveInterval;

    #trackActivity = () => {
        this.lastUpdatedAt = Date.now();
        this.alive = true;
    };

    /**
     * @type {BuildEventListener}
     */
    #startListener = () => {
        this.#trackActivity();
        this.#logger.info("⏰ Build started...");
    };

    #internalErrorListener = () => {
        this.errorCount += 1;

        if (this.errorCount > 100) {
            clearTimeout(this.#keepAliveInterval);

            this.close();
            this.#logger.info("⛔️ Closing connection");
        }
    };

    /**
     * @type {BuildEventListener<string>}
     */
    #errorListener = (event) => {
        this.#trackActivity();

        this.#logger.warn("⛔️⛔️⛔️  Build error...");

        /**
         * @type {ESBuildMessage[]}
         */
        const esbuildErrorMessages = JSON.parse(event.data);

        for (const error of esbuildErrorMessages) {
            this.#logger.warn(error.text);

            if (error.location) {
                this.#logger.debug(
                    `file://${error.location.file}:${error.location.line}:${error.location.column}`,
                );
                this.#logger.debug(error.location.lineText);
            }
        }
    };

    /**
     * @type {BuildEventListener}
     */
    #endListener = () => {
        cancelAnimationFrame(this.#reloadFrameID);

        this.#trackActivity();

        if (!this.online) {
            this.#logger.info("🚫 Build finished while offline.");
            this.deferredReload = true;

            return;
        }

        this.#logger.info("🛎️ Build completed! Reloading...");

        // We use an animation frame to keep the reload from happening before the
        // event loop has a chance to process the message.
        this.#reloadFrameID = requestAnimationFrame(() => {
            window.location.reload();
        });
    };

    /**
     * @type {BuildEventListener}
     */
    #keepAliveListener = () => {
        this.#trackActivity();
        this.#logger.info("🏓 Keep-alive");
    };

    /**
     * Initialize the ESBuild observer.
     * This should be called once in your application.
     *
     * @param {string | URL} [url]
     * @returns {ESBuildObserver}
     */
    static initialize = (url) => {
        const esbuildObserver = new ESBuildObserver(url);

        return esbuildObserver;
    };

    /**
     *
     * @param {string | URL} [url]
     * @param {Logger} [logger]
     */
    constructor(url, logger = createLogger()) {
        if (!url) {
            throw new TypeError("ESBuildObserver: Cannot construct without a URL");
        }

        super(url);

        this.#logger = logger;

        this.addEventListener("esbuild:start", this.#startListener);
        this.addEventListener("esbuild:end", this.#endListener);
        this.addEventListener("esbuild:error", this.#errorListener);
        this.addEventListener("esbuild:keep-alive", this.#keepAliveListener);

        this.addEventListener("error", this.#internalErrorListener);

        window.addEventListener("offline", () => {
            this.online = false;
        });

        window.addEventListener("online", () => {
            this.online = true;

            if (!this.deferredReload) return;

            this.#logger.info("🛎️ Reloading after offline build...");
            this.deferredReload = false;

            window.location.reload();
        });

        this.#logger.info("🛎️ Listening for build changes...");

        this.#keepAliveInterval = setInterval(() => {
            const now = Date.now();

            if (now - this.lastUpdatedAt < 10_000) return;

            this.alive = false;
            this.#logger.info("👋 Waiting for build to start...");
        }, 15_000);
    }

    [Symbol.dispose]() {
        return this.close();
    }

    dispose() {
        return this[Symbol.dispose]();
    }
}

export default ESBuildObserver;
