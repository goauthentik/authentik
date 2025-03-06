/**
 * @file
 * Client-side observer for ESBuild events.
 */
import type { Message as ESBuildMessage } from "esbuild";

const logPrefix = "👷 [ESBuild]";
const log = console.debug.bind(console, logPrefix);

type BuildEventListener<Data = unknown> = (event: MessageEvent<Data>) => void;

/**
 * A client-side watcher for ESBuild.
 *
 * Note that this should be conditionally imported in your code, so that
 * ESBuild may tree-shake it out of production builds.
 *
 * ```ts
 * if (process.env.NODE_ENV === "development" && process.env.WATCHER_URL) {
 *   const { ESBuildObserver } = await import("@goauthentik/common/client");
 *
 *   new ESBuildObserver(process.env.WATCHER_URL);
 * }
 * ```
}

 */
export class ESBuildObserver extends EventSource {
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
     */
    #keepAliveInterval: ReturnType<typeof setInterval> | undefined;

    #trackActivity = () => {
        this.lastUpdatedAt = Date.now();
        this.alive = true;
    };

    #startListener: BuildEventListener = () => {
        this.#trackActivity();
        log("⏰  Build started...");
    };

    #internalErrorListener = () => {
        this.errorCount += 1;

        if (this.errorCount > 100) {
            clearTimeout(this.#keepAliveInterval);

            this.close();
            log("⛔️  Closing connection");
        }
    };

    #errorListener: BuildEventListener<string> = (event) => {
        this.#trackActivity();

        // eslint-disable-next-line no-console
        console.group(logPrefix, "⛔️⛔️⛔️  Build error...");

        const esbuildErrorMessages: ESBuildMessage[] = JSON.parse(event.data);

        for (const error of esbuildErrorMessages) {
            console.warn(error.text);

            if (error.location) {
                console.debug(
                    `file://${error.location.file}:${error.location.line}:${error.location.column}`,
                );
                console.debug(error.location.lineText);
            }
        }

        // eslint-disable-next-line no-console
        console.groupEnd();
    };

    #endListener: BuildEventListener = () => {
        cancelAnimationFrame(this.#reloadFrameID);

        this.#trackActivity();

        if (!this.online) {
            log("🚫  Build finished while offline.");
            this.deferredReload = true;

            return;
        }

        log("🛎️  Build completed! Reloading...");

        // We use an animation frame to keep the reload from happening before the
        // event loop has a chance to process the message.
        this.#reloadFrameID = requestAnimationFrame(() => {
            window.location.reload();
        });
    };

    #keepAliveListener: BuildEventListener = () => {
        this.#trackActivity();
        log("🏓 Keep-alive");
    };

    constructor(url: string | URL) {
        super(url);

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

            log("🛎️  Reloading after offline build...");
            this.deferredReload = false;

            window.location.reload();
        });

        log("🛎️  Listening for build changes...");

        this.#keepAliveInterval = setInterval(() => {
            const now = Date.now();

            if (now - this.lastUpdatedAt < 10_000) return;

            this.alive = false;
            log("👋  Waiting for build to start...");
        }, 15_000);
    }
}
