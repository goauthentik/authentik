/**
 * @file Storage utilities.
 */

/**
 * A utility class for safely accessing web storage (localStorage or sessionStorage) with error handling.
 */
export class StorageAccessor {
    constructor(
        public readonly key: string,
        protected readonly storage: Storage,
    ) {}

    public static local = (key: string) => new StorageAccessor(key, localStorage);
    public static session = (key: string) => new StorageAccessor(key, sessionStorage);

    public read(): string | null {
        try {
            return this.storage.getItem(this.key);
        } catch (_error: unknown) {
            return null;
        }
    }

    public write(value: string): boolean {
        try {
            this.storage.setItem(this.key, value);
            return true;
        } catch (_error: unknown) {
            return false;
        }
    }

    public delete(): boolean {
        try {
            this.storage.removeItem(this.key);
            return true;
        } catch (_error: unknown) {
            return false;
        }
    }
}
