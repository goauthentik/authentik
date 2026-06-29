/**
 * @file Object utilities.
 */

/**
 * Utility to remove a key from an object, returning a new object. This is used to remove error keys when a form is updated.
 *
 * @param input The object to remove the key from.
 * @param keyToDelete The key to remove from the object.
 * @returns A new object with the key removed, or undefined if the input is falsy.
 */
export function omitKeys<T extends object, K extends keyof T>(
    input: T,
    ...omittedKeys: K[]
): Omit<T, K> | undefined {
    if (!input) {
        return undefined;
    }

    const result: Partial<T> = {};
    const omittedKeysSet = new Set(omittedKeys);

    for (const [key, value] of Object.entries(input)) {
        if (omittedKeysSet.has(key as K)) {
            continue;
        }

        // Skip if value is undefined or empty array.
        const empty = typeof value === "undefined" || (Array.isArray(value) && value.length === 0);

        if (empty) {
            continue;
        }

        result[key as keyof T] = value;
    }

    return result as Omit<T, K>;
}

/**
 * Given an object and a list of keys, trim the string values of those keys
 * in the object and return a new object with the trimmed values. Non-string values are returned as-is.
 *
 * @param target The object to trim values from.
 * @param keys The keys of the object to trim.
 * @returns A new object with the specified keys trimmed.
 */
export function trimMany<T extends object, K extends keyof T>(target: T, ...keys: K[]): Pick<T, K> {
    const output = {} as Record<K, unknown>;

    for (const key of keys) {
        const value = target[key];

        output[key] = typeof value === "string" ? value.trim() : value;
    }

    return output as Pick<T, K>;
}
