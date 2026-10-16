/**
 * @file The page's handle on the search worker. `openSearchDatabase` starts `worker.mjs` by URL
 *   and resolves once the index is open; the handle it returns runs statements in the worker.
 */

import { SEARCH_WORKER_FILENAME, SQLITE_RUNTIME_MODULE_FILENAME } from "./common.mjs";

/**
 * @import { SearchDatabase, SQLValue } from "./query.mjs";
 */

/**
 * @typedef {SearchDatabase & { terminate: () => void }} SearchWorkerClient
 */

/**
 * @typedef {{ resolve: (value: unknown) => void; reject: (error: Error) => void }} Waiter
 */

/**
 * Starts the worker at `workerURL` and routes each call to its reply by id.
 *
 * @param {string} workerURL
 *
 * @returns {{
 *     call: (request: Record<string, unknown>) => Promise<unknown>;
 *     terminate: () => void;
 * }}
 */
function startWorker(workerURL) {
    const worker = new Worker(workerURL, { type: "module" });

    /** @type {Map<number, Waiter>} */
    const pending = new Map();
    let nextID = 0;

    worker.addEventListener(
        "message",
        (/** @type {MessageEvent<{ id: number; result?: unknown; error?: string }>} */ event) => {
            const reply = event.data;
            const waiter = pending.get(reply.id);

            if (!waiter) return;

            pending.delete(reply.id);

            if (typeof reply.error === "string") {
                waiter.reject(new Error(reply.error));
            } else {
                waiter.resolve(reply.result);
            }
        },
    );

    worker.addEventListener("error", (event) => {
        const error = new Error(
            event.message || `The search worker at ${workerURL} failed to load`,
        );

        for (const waiter of pending.values()) {
            waiter.reject(error);
        }

        pending.clear();
    });

    return {
        call(request) {
            return new Promise((resolve, reject) => {
                const id = nextID++;

                pending.set(id, { resolve, reject });
                worker.postMessage({ ...request, id });
            });
        },
        terminate() {
            worker.terminate();
        },
    };
}

/**
 * @param {string} runtimeBaseURL
 *
 * @returns {URL}
 */
function runtimeBase(runtimeBaseURL) {
    return new URL(
        runtimeBaseURL.endsWith("/") ? runtimeBaseURL : `${runtimeBaseURL}/`,
        globalThis.location.href,
    );
}

/**
 * Opens the index at `databaseURL` in a worker that loads the sqlite-wasm runtime from
 * `runtimeBaseURL`, the same-origin directory the build staged it into.
 *
 * @param {string} databaseURL
 * @param {string} runtimeBaseURL
 *
 * @returns {Promise<SearchWorkerClient>}
 */
export async function openSearchDatabase(databaseURL, runtimeBaseURL) {
    const base = runtimeBase(runtimeBaseURL);
    const worker = startWorker(new URL(SEARCH_WORKER_FILENAME, base).href);

    try {
        await worker.call({
            type: "open",
            databaseURL: new URL(databaseURL, globalThis.location.href).href,
            runtimeModuleURL: new URL(SQLITE_RUNTIME_MODULE_FILENAME, base).href,
        });

        return {
            query(sql, parameters = []) {
                return /** @type {Promise<Record<string, SQLValue>[]>} */ (
                    worker.call({ type: "query", sql, parameters })
                );
            },
            terminate: worker.terminate,
        };
    } catch (error) {
        worker.terminate();
        throw error;
    }
}
