/**
 * @file Shared types for client-side storage.
 */

// #region Types

/**
 * Templated string representing a persistence key managed by authentik.
 *
 * ```ts
 * export const PERSISTENCE_KEY_LOCALE = "ak:locale" satisfies PersistenceKey;
 *
 * // Key with a namespace:
 * export const PERSISTENCE_KEY_USER_EMAIL_ADDRESS =
 *     "ak:user:email_address" satisfies PersistenceKey;
 * ```
 */
export type PersistenceKey = `ak:${string}` | `ak_${string}`;

// #endregion

// #region Helpers

/**
 * In-memory implementation of the `Storage` interface.
 *
 * This is useful for testing or environments without a native `localStorage`.
 */
export class MemoryStorage implements Storage {
    #items = new Map<string, string>();

    public get length() {
        return this.#items.size;
    }

    public key(index: number) {
        return [...this.#items.keys()][index] ?? null;
    }

    public getItem(key: string) {
        return this.#items.get(key) ?? null;
    }

    public setItem(key: string, value: string) {
        this.#items.set(key, value);
    }

    public removeItem(key: string) {
        this.#items.delete(key);
    }

    public clear() {
        this.#items.clear();
    }
}

// #endregion
