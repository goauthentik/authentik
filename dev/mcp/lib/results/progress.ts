/**
 * @file Progress reporting shared by long-running checks.
 */

/**
 * `done` steps of `total` are finished; `message` names what's happening now.
 */
export type Progress = (done: number, total: number, message: string) => void;

export const noProgress: Progress = () => {};

/**
 * A counter for steps that finish in any order, such as checks run with `Promise.all`.
 *
 * Call `step(name)` around each one; each finish reports what has completed so far.
 */
export function counter(progress: Progress, total: number) {
    let done = 0;

    return async function step<T>(name: string, work: Promise<T>): Promise<T> {
        const value = await work;

        done++;

        progress(done, total, `${name} done (${done} of ${total})`);

        return value;
    };
}
