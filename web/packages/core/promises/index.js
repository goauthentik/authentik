/**
 * @file Helpers for running tests.
 */

/**
 * A function that returns a promise.
 * @template {never[]} [A=never[]]
 * @typedef {(...args: A) => Promise<unknown>} Thenable
 */

/**
 * A tuple of a function and its arguments.
 * @template {Thenable} [T=Thenable]
 * @typedef {[T, Parameters<T>]} SerializedThenable
 */

/**
 * Executes a sequence of promise-returning functions in series
 * @template {Thenable[]} T
 * @param {{ [K in keyof T]: [T[K], ...Parameters<T[K]>] }} sequence
 * @returns {Promise<void>}
 */
export async function series(...sequence) {
    for (const [thenable, ...args] of sequence) {
        await thenable(...args);
    }
}
