/**
 * Given an object and a key, returns the trimmed string value of the key if it exists, otherwise returns null.
 *
 * @param item The object to pluck the name from.
 * @param key The key to look for in the object, defaults to "name".
 * @returns The trimmed string value of the key if it exists, otherwise null.
 */
export function pluckEntityName<T extends object, K extends Extract<keyof T, string>>(
    item?: T | null,
    key: K = "name" as K,
): string | null {
    if (typeof item !== "object" || item === null) {
        return null;
    }

    if (!(key in item)) {
        return null;
    }

    return typeof item[key] === "string" ? item[key].trim() : null;
}
