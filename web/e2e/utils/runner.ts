/**
 * @file Helpers for running tests.
 */

/**
 * A function that returns a promise.
 */
export type Thenable = (...args: never[]) => Promise<void>;

/**
 * Given a function that returns a promise, return a function which invokes the promise.
 *
 * @see {@linkcode series} for usage.
 *
 * @param thenable The function to invoke.
 * @param args The arguments to pass to the function.
 */
export function P<T extends Thenable = Thenable>(
    thenable: T,
    ...args: Parameters<T>
): () => Promise<void> {
    return () => thenable(...args);
}

/**
 * Run a series of promises in order.
 *
 * ```ts
 * await series(
 *     P(form.fillTextField, "name", providerName, $providerForm),
 *     P(form.setFormGroup, "Flow settings", true),
 * )
 * ```
 *
 * @param steps The promises to run.
 */
export async function series(...steps: Thenable[]): Promise<void> {
    for (const step of steps) {
        await step();
    }
}
