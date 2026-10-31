/**
 * @file Constants and types shared by the search index builder, the query code and the modal.
 *   The index is one gzip-compressed SQLite file per site build. It holds one record per
 *   heading-scoped section and per named table row of every page of every site, so a reader
 *   on any site can find a page on any other.
 */

export const PLUGIN_NAME = "ak-search-plugin";

/**
 * The directory under a site's `static/` where the index and the sqlite-wasm runtime are staged,
 * and therefore the URL path the browser fetches them from.
 */
export const SEARCH_DIRECTORY = "search";

export const SEARCH_INDEX_FILENAME = "search-index.db.gz";

/**
 * The worker script the page starts by URL. It imports the sqlite-wasm runtime staged beside it.
 */
export const SEARCH_WORKER_FILENAME = "worker.mjs";

/**
 * The files of `@sqlite.org/sqlite-wasm` the worker loads by URL.
 *
 * The runtime module finds `sqlite3.wasm` beside itself through `import.meta.url`, and requests
 * the OPFS proxy on a cross-origin-isolated page even though this index never opens OPFS.
 */
export const SQLITE_RUNTIME_MODULE_FILENAME = "index.mjs";

/**
 * The runtime is staged under a directory named for its version, so a `_headers` rule can mark
 * those files immutable while the index and the worker at the directory above are revalidated.
 *
 * @param {string} version The `@sqlite.org/sqlite-wasm` package version.
 *
 * @returns {string}
 */
export function sqliteRuntimeDirectory(version) {
    return `sqlite-wasm-${version}`;
}
export const SQLITE_RUNTIME_FILES = [
    SQLITE_RUNTIME_MODULE_FILENAME,
    "sqlite3.wasm",
    "sqlite3-opfs-async-proxy.js",
];

/**
 * The number of hierarchy entries: the category, then `h1` through `h6`.
 */
export const HIERARCHY_DEPTH = 7;

/**
 * The hierarchy level a table-row record is written at. The indexer writes it and the ranker
 * reads it. Pages rarely use `h5`, so a row's name sits where a heading of that depth would.
 */
export const TABLE_ROW_LEVEL = 5;

/**
 * @typedef {object} SearchSite
 * @property {string} id A short identifier, such as `docs`.
 * @property {string} label The name readers see, such as `Documentation`.
 * @property {string} directory The site's source directory, relative to `website/`.
 * @property {string} url The origin the site is published at.
 * @property {string} routeBasePath The docs plugin's `routeBasePath`.
 * @property {readonly (readonly [string, string])[]} [categories] `[slug, label]` pairs naming
 *   the top-level source directories. A directory without an entry is title-cased.
 * @property {string} [category] One label for every page of the site, instead of a label per
 *   top-level directory.
 * @property {string[]} [ignoreFiles] Glob patterns, relative to the site directory, of source
 *   files that are not pages.
 */

/**
 * @typedef {object} SearchRecord
 * @property {string} id At build time, the first 32 hex characters of a SHA-256 over the site,
 *   URL, anchor and position, which the writer checks for duplicates; in a query result, the
 *   record's rowid.
 * @property {string} site The label of the site the record belongs to.
 * @property {string} url The page's path, relative for the site being built and absolute for the
 *   other sites.
 * @property {string} anchor The heading id the record links to, or the empty string for the top
 *   of the page.
 * @property {(string | null)[]} hierarchy Seven entries, the category then `h1` through `h6`,
 *   with `null` below the record's own level.
 * @property {string} content The text under the heading, or the empty string for a heading
 *   without body text.
 * @property {number} level The depth of the deepest non-null hierarchy entry, 1 through 6.
 * @property {number} position The zero-based order of the record on its page.
 */

/**
 * @typedef {object} SearchHit
 * @property {string} site
 * @property {string} url
 * @property {string} anchor
 * @property {(string | null)[]} hierarchy
 * @property {string} snippet At most {@link SNIPPET_LENGTH} characters of content around the
 *   first match.
 * @property {[start: number, end: number][]} highlights Character ranges within `snippet` that
 *   matched a query token.
 */

/**
 * @typedef {object} SearchResponse
 * @property {string} query
 * @property {string | null} corrected The text the search ran on when a token was corrected
 *   against the vocabulary, or `null` when none was.
 * @property {SearchHit[]} hits
 */

/**
 * The most characters a hit's excerpt holds.
 */
export const SNIPPET_LENGTH = 160;

/**
 * The data the plugin publishes for the search bar through `usePluginData`.
 *
 * @typedef {object} SearchGlobalData
 * @property {string} site The label of the site being served.
 * @property {string} indexPath The site-relative path of the gzip index.
 * @property {string} workerPath The site-relative path of the worker script.
 * @property {string} runtimePath The site-relative directory of the sqlite-wasm
 *   runtime.
 */

/**
 * The site-relative link for a hit.
 *
 * @param {Pick<SearchHit, "url" | "anchor">} hit
 *
 * @returns {string}
 */
export function hitHref(hit) {
    return hit.anchor === "" ? hit.url : `${hit.url}#${hit.anchor}`;
}
