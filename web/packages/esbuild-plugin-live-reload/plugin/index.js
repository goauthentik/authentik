/**
 * @file Live reload plugin for ESBuild.
 *
 * @import { ListenOptions } from "node:net";
 * @import {Server as HTTPServer} from "node:http";
 * @import {Server as HTTPSServer} from "node:https";
 */
import { findFreePorts } from "find-free-ports";
import * as http from "node:http";
import * as path from "node:path";

/**
 * Serializes a custom event to a text stream.
 * @param {Event} event
 * @returns {string}
 */
export function serializeCustomEventToStream(event) {
    // @ts-expect-error - TS doesn't know about the detail property
    const data = event.detail ?? {};

    const eventContent = [`event: ${event.type}`, `data: ${JSON.stringify(data)}`];

    return eventContent.join("\n") + "\n\n";
}

const MIN_PORT = 1025;
const MAX_PORT = 65535;

/**
 * Find a random port that is not in use, sufficiently far from the default port.
 * @returns {Promise<number>}
 */
async function findDisparatePort() {
    const startPort = Math.floor(Math.random() * (MAX_PORT - MIN_PORT + 1)) + MIN_PORT;

    const wathcherPorts = await findFreePorts(1, {
        startPort,
    });

    const [port] = wathcherPorts;

    if (!port) {
        throw new Error("No free ports available");
    }

    return port;
}

/**
 * Event server initialization options.
 *
 * @typedef {Object} EventServerInit
 *
 * @property {string} pathname
 * @property {EventTarget} dispatcher
 * @property {string} [logPrefix]
 */

/**
 * @typedef {(req: http.IncomingMessage, res: http.ServerResponse) => void} RequestHandler
 */

/**
 * Create an event request handler.
 * @param {EventServerInit} options
 * @returns {RequestHandler}
 * @category ESBuild
 */
export function createRequestHandler({ pathname, dispatcher, logPrefix = "Build Observer" }) {
    // eslint-disable-next-line no-console
    const log = console.log.bind(console, `[${logPrefix}]`);

    /**
     * @type {RequestHandler}
     */
    const requestHandler = (req, res) => {
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET");
        res.setHeader("Access-Control-Allow-Headers", "Content-Type");

        if (req.url !== pathname) {
            log(`🚫 Invalid request to ${req.url}`);
            res.writeHead(404);
            res.end();
            return;
        }

        log("🔌 Client connected");

        res.writeHead(200, {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        });

        /**
         * @param {Event} event
         */
        const listener = (event) => {
            const body = serializeCustomEventToStream(event);

            res.write(body);
        };

        dispatcher.addEventListener("esbuild:start", listener);
        dispatcher.addEventListener("esbuild:error", listener);
        dispatcher.addEventListener("esbuild:end", listener);

        req.on("close", () => {
            log("🔌 Client disconnected");

            clearInterval(keepAliveInterval);

            dispatcher.removeEventListener("esbuild:start", listener);
            dispatcher.removeEventListener("esbuild:error", listener);
            dispatcher.removeEventListener("esbuild:end", listener);
        });

        const keepAliveInterval = setInterval(() => {
            console.timeStamp("🏓 Keep-alive");

            res.write("event: keep-alive\n\n");
            res.write(serializeCustomEventToStream(new CustomEvent("esbuild:keep-alive")));
        }, 15_000);
    };

    return requestHandler;
}

/**
 * Options for the build observer plugin.
 *
 * @typedef {object} BuildObserverOptions
 *
 * @property {HTTPServer | HTTPSServer} [server]
 * @property {ListenOptions} [listenOptions]
 * @property {string | URL} [publicURL]
 * @property {string} [logPrefix]
 * @property {string} [relativeRoot]
 */

/**
 * Creates a plugin that listens for build events and sends them to a server-sent event stream.
 *
 * @param {BuildObserverOptions} [options]
 * @returns {import('esbuild').Plugin}
 */
export function liveReloadPlugin(options = {}) {
    return {
        name: "build-watcher",
        setup: async (build) => {
            const logPrefix = options.logPrefix || "Build Observer";

            const timerLabel = `[${logPrefix}] 🏁`;
            const relativeRoot = options.relativeRoot || process.cwd();

            const dispatcher = new EventTarget();

            /**
             * @type {URL}
             */
            let publicURL;

            if (!options.publicURL) {
                const port = await findDisparatePort();

                publicURL = new URL(`http://localhost:${port}/events`);
            } else {
                publicURL =
                    typeof options.publicURL === "string"
                        ? new URL(options.publicURL)
                        : options.publicURL;
            }

            build.initialOptions.define = {
                ...build.initialOptions.define,
                "import.meta.env.ESBUILD_WATCHER_URL": JSON.stringify(publicURL.href),
            };

            const requestHandler = createRequestHandler({
                pathname: publicURL.pathname,
                dispatcher,
                logPrefix,
            });

            const server = options.server || http.createServer(requestHandler);

            const listenOptions = options.listenOptions || {
                port: parseInt(publicURL.port, 10),
                host: publicURL.hostname,
            };

            server.listen(listenOptions, () => {
                // eslint-disable-next-line no-console
                console.log(`[${logPrefix}] Listening`);
            });

            build.onDispose(() => {
                server?.close();
            });

            build.onStart(() => {
                console.time(timerLabel);

                dispatcher.dispatchEvent(
                    new CustomEvent("esbuild:start", {
                        detail: new Date().toISOString(),
                    }),
                );
            });

            build.onEnd((buildResult) => {
                console.timeEnd(timerLabel);

                if (!buildResult.errors.length) {
                    dispatcher.dispatchEvent(
                        new CustomEvent("esbuild:end", {
                            detail: new Date().toISOString(),
                        }),
                    );

                    return;
                }

                console.warn(`Build ended with ${buildResult.errors.length} errors`);

                dispatcher.dispatchEvent(
                    new CustomEvent("esbuild:error", {
                        detail: buildResult.errors.map((error) => ({
                            ...error,
                            location: error.location
                                ? {
                                      ...error.location,
                                      file: path.resolve(relativeRoot, error.location.file),
                                  }
                                : null,
                        })),
                    }),
                );
            });
        },
    };
}
