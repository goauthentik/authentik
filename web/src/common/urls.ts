/**
 * @file URLs of authentik resources, resolved below the web base path so they
 *   keep working when authentik runs under `AUTHENTIK_WEB__PATH`.
 */

import { globalAK } from "#common/global";

/**
 * The URL of an authentik websocket endpoint.
 *
 * @remarks
 *   The session cookie is scoped to the web base path too, so a websocket
 *   outside of it would not be authenticated either.
 * @param path The endpoint's path below the web base path, e.g. `ws/client/`.
 */
export function websocketURL(path: string): string {
    const url = new URL(path, globalAK().api.base);
    url.protocol = window.location.protocol.replace("http", "ws");

    return url.href;
}

/**
 * The URL of a file the server ships.
 *
 * @remarks
 *   Must match `StaticBackend.file_url` in `authentik/admin/files/backends/static.py`.
 * @param name The file's path as the server names it, e.g. `/static/dist/assets/icons/icon.png`.
 */
export function staticURL(name: string): string {
    return globalAK().api.relBase.replace(/\/$/, "") + name;
}
