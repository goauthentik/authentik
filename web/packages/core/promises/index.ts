/**
 * @file Helpers for running tests.
 */

/**
 * A function that returns a promise.
 */
export type Thenable<A extends never[] = never[]> = (...args: A) => Promise<unknown>;

/**
 * A tuple of a function and its arguments.
 */
export type SerializedThenable<T extends Thenable = Thenable> = [T, Parameters<T>];

/**
 * Executes a sequence of promise-returning functions in series
 */
export async function series<T extends Thenable[]>(
    ...sequence: { [K in keyof T]: [T[K], ...Parameters<T[K]>] }
): Promise<void> {
    for (const [thenable, ...args] of sequence) {
        await thenable(...args);
    }
}
