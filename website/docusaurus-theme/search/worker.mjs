/**
 * @file The dedicated worker that holds the search index. It fetches the gzip SQLite file once,
 *   inflates it, opens the bytes in memory through `@sqlite.org/sqlite-wasm`, and answers query
 *   messages from the page.
 *   The build stages this file beside the sqlite-wasm runtime and the page loads it by URL, so no
 *   bundler ever sees it. It therefore imports nothing at module scope: the runtime module's URL
 *   arrives in the open message.
 */

/**
 * @import { Database, PreparedStatement, Sqlite3Static } from "@sqlite.org/sqlite-wasm";
 */

/**
 * A value SQLite can bind to a statement parameter or return in a result column. The staged copy
 * of this file stands alone, so the type is declared here rather than imported from `query.mjs`.
 *
 * @typedef {string | number | bigint | Uint8Array | null} SQLValue
 */

/**
 * @typedef {{ id: number; type: "open"; databaseURL: string; runtimeModuleURL: string }} OpenCall
 *
 * @typedef {{ id: number; type: "query"; sql: string; parameters: readonly SQLValue[] }} QueryCall
 *
 * @typedef {OpenCall | QueryCall} WorkerCall
 *
 * @typedef {{ id: number; result: unknown } | { id: number; error: string }} WorkerReply
 */

/**
 * The number of prepared statements kept between queries.
 */
const STATEMENT_CACHE_LIMIT = 16;

/** @type {Database | null} */
let database = null;

/** @type {Map<string, PreparedStatement>} */
const statements = new Map();

/**
 * @param {string} url
 *
 * @returns {Promise<Uint8Array>}
 */
async function fetchWhole(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`${url} returned HTTP ${response.status}`);
    }

    const bytes = new Uint8Array(await response.arrayBuffer());

    // A body that starts with the gzip magic number is inflated here. A body the browser already
    // inflated under `Content-Encoding: gzip` is used as it is.
    if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return bytes;

    const inflated = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));

    return new Uint8Array(await new Response(inflated).arrayBuffer());
}

/**
 * @param {Sqlite3Static} sqlite3
 * @param {Uint8Array} bytes
 *
 * @returns {Database}
 */
function openInMemory(sqlite3, bytes) {
    const db = new sqlite3.oo1.DB(":memory:", "c");
    const pointer = sqlite3.wasm.alloc(bytes.byteLength);

    sqlite3.wasm.heap8u().set(bytes, pointer);

    const rc = sqlite3.capi.sqlite3_deserialize(
        /** @type {number} */ (db.pointer),
        "main",
        pointer,
        bytes.byteLength,
        bytes.byteLength,
        sqlite3.capi.SQLITE_DESERIALIZE_FREEONCLOSE | sqlite3.capi.SQLITE_DESERIALIZE_READONLY,
    );

    if (rc !== sqlite3.capi.SQLITE_OK) {
        sqlite3.wasm.dealloc(pointer);
        db.close();
        throw new Error(`sqlite3_deserialize failed: ${sqlite3.capi.sqlite3_js_rc_str(rc)}`);
    }

    return db;
}

/**
 * @param {OpenCall} call
 *
 * @returns {Promise<{ sqliteVersion: string }>}
 */
async function open(call) {
    const runtime = /** @type {typeof import("@sqlite.org/sqlite-wasm")} */ (
        await import(/* webpackIgnore: true */ call.runtimeModuleURL)
    );

    // The published type of the initializer declares no parameter; the runtime accepts the
    // Emscripten module options.
    const initialize = /** @type {(options: Record<string, unknown>) => Promise<Sqlite3Static>} */ (
        runtime.default
    );

    const sqlite3 = await initialize({
        print: () => {},
        printErr: (/** @type {string} */ message) => console.error("[sqlite-wasm]", message),
    });

    database = openInMemory(sqlite3, await fetchWhole(call.databaseURL));

    return { sqliteVersion: sqlite3.capi.sqlite3_libversion() };
}

/**
 * @param {string} sql
 *
 * @returns {PreparedStatement}
 */
function prepared(sql) {
    if (!database) throw new Error("The search index is not open");

    let statement = statements.get(sql);

    if (statement) return statement;

    if (statements.size >= STATEMENT_CACHE_LIMIT) {
        const oldest = statements.entries().next().value;

        if (oldest) {
            oldest[1].finalize();
            statements.delete(oldest[0]);
        }
    }

    statement = database.prepare(sql);
    statements.set(sql, statement);

    return statement;
}

/**
 * @param {QueryCall} call
 *
 * @returns {Record<string, SQLValue>[]}
 */
function query(call) {
    const statement = prepared(call.sql);

    /** @type {Record<string, SQLValue>[]} */
    const rows = [];

    try {
        if (call.parameters.length) {
            statement.bind(/** @type {SQLValue[]} */ ([...call.parameters]));
        }

        while (statement.step()) {
            rows.push(/** @type {Record<string, SQLValue>} */ (statement.get({})));
        }
    } finally {
        statement.reset(true);
    }

    return rows;
}

/**
 * @param {WorkerCall} call
 *
 * @returns {Promise<unknown>}
 */
async function answer(call) {
    switch (call.type) {
        case "open":
            return open(call);
        case "query":
            return query(call);
        default:
            throw new Error(`Unknown search worker call ${JSON.stringify(call)}`);
    }
}

globalThis.addEventListener("message", (/** @type {MessageEvent<WorkerCall>} */ event) => {
    const call = event.data;

    /**
     * @param {WorkerReply} message
     */
    const reply = (message) => globalThis.postMessage(message);

    answer(call).then(
        (result) => reply({ id: call.id, result }),
        (/** @type {unknown} */ error) =>
            reply({ id: call.id, error: error instanceof Error ? error.message : String(error) }),
    );
});
