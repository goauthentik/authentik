import * as http from "http";
import path from "path";

/**
 * Serializes a custom event to a text stream.
 * a
 * @param {Event} event
 * @returns {string}
 */
export function serializeCustomEventToStream(event) {
    // @ts-expect-error - TS doesn't know about the detail property
    const data = event.detail ?? {};

    const eventContent = [`event: ${event.type}`, `data: ${JSON.stringify(data)}`];

    return eventContent.join("\n") + "\n\n";
}

/**
 * Options for the build observer plugin.
 *
 * @typedef {Object} BuildObserverOptions
 *
 * @property {URL} serverURL
 * @property {string} logPrefix
 * @property {string} relativeRoot
 */

/**
 * Creates a plugin that listens for build events and sends them to a server-sent event stream.
 *
 * @param {BuildObserverOptions} options
 * @returns {import('esbuild').Plugin}
 */
export function buildObserverPlugin({ serverURL, logPrefix, relativeRoot }) {
    const timerLabel = `[${logPrefix}] Build`;
    const endpoint = serverURL.pathname;
    const dispatcher = new EventTarget();

    const eventServer = http.createServer((req, res) => {
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET");
        res.setHeader("Access-Control-Allow-Headers", "Content-Type");

        if (req.url !== endpoint) {
            console.log(`🚫 Invalid request to ${req.url}`);
            res.writeHead(404);
            res.end();
            return;
        }

        console.log("🔌 Client connected");

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
            console.log("🔌 Client disconnected");

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
    });

    return {
        name: "build-watcher",
        setup: (build) => {
            eventServer.listen(parseInt(serverURL.port, 10), serverURL.hostname);

            build.onDispose(() => {
                eventServer.close();
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
