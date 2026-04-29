/**
 * @file Promise utilities.
 */

/**
 * Type predicate to determine if an object is thenable (i.e., has a `then` method).
 */
export function isPromiseLike<T>(obj: unknown): obj is PromiseLike<T> {
    if (!obj || typeof obj !== "object") {
        return false;
    }
    return typeof (obj as Promise<T>).then === "function";
}
