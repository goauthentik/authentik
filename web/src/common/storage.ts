/**
 * @file Storage utilities.
 */

import { ConsoleLogger } from "#logger/browser";

/**
 * A utility class for safely accessing web storage (localStorage or sessionStorage) with error handling.
 */
export class StorageAccessor {
    constructor(
        /**
         * The key under which the value is stored in the storage backend.
         */
        public readonly key: string,
        /**
         * The storage backend to use, e.g. `window.localStorage` or `window.sessionStorage`.
         */
        protected readonly storage: Storage,
        protected logger = ConsoleLogger.prefix("storage-accessor"),
    ) {
        if (typeof key !== "string") {
            throw new TypeError("Storage key must be a string");
        }

        if (!key) {
            throw new TypeError("Storage key must be a non-empty string");
        }
    }

    /**
     * Create a {@link StorageAccessor} for local storage.
     *
     * @param key The key under which the value is stored in localStorage.
     */
    public static local = (key: string) => new StorageAccessor(key, self.localStorage);
    /**
     * Create a {@link StorageAccessor} for session storage.
     *
     * @param key The key under which the value is stored in sessionStorage.
     */
    public static session = (key: string) => new StorageAccessor(key, self.sessionStorage);

    /**
     * Read the value from storage.
     *
     * @param fallback An optional value to return if the key does not exist or an error occurs. Defaults to `null`.
     *
     * @returns The stored value, or `null` if the key does not exist or an error occurs.
     */
    public read<T extends string>(fallback?: T): T | null {
        try {
            const value = this.storage.getItem(this.key);
            return value !== null ? (value as T) : (fallback ?? null);
        } catch (_error: unknown) {
            return fallback ?? null;
        }
    }

    /**
     * Write a value to storage.
     *
     * @param value The value to store.
     *
     * @returns `true` if the value was successfully stored, or `false` if an error occurred.
     */
    public write(value: string | null): boolean {
        if (!value) {
            if (this.read()) {
                return this.delete();
            }

            return true;
        }

        try {
            this.storage.setItem(this.key, value);
            return true;
        } catch (_error: unknown) {
            return false;
        }
    }

    /**
     * Read the value from storage and parse it as JSON.
     *
     * @param fallback An optional value to return if the key does not exist, the value is not valid JSON, or an error occurs. Defaults to `null`.
     *
     * @returns The parsed value, or `null` if the key does not exist, the value is not valid JSON, or an error occurs.
     */
    public readJSON<T>(fallback?: T): T | null {
        const value = this.read<string>();

        if (value === null) {
            return fallback ?? null;
        }

        try {
            return JSON.parse(value) as T;
        } catch (_error: unknown) {
            return fallback ?? null;
        }
    }

    /**
     * Write a value to storage after stringifying it as JSON.
     *
     * @param value The value to store.
     *
     * @returns `true` if the value was successfully stored, or `false` if an error occurred.
     */
    public writeJSON(value: unknown): boolean {
        try {
            const stringified = JSON.stringify(value);
            return this.write(stringified);
        } catch (error: unknown) {
            this.logger.error("Failed to write JSON value to storage", error);

            return false;
        }
    }

    /**
     * Delete the value from storage.
     *
     * @returns `true` if the value was successfully deleted, or `false` if an error occurred.
     */
    public delete(): boolean {
        this.logger.debug("Deleting value from storage");

        try {
            this.storage.removeItem(this.key);
            return true;
        } catch (error: unknown) {
            this.logger.error("Failed to delete value from storage", error);

            return false;
        }
    }
}
