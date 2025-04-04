/**
 * Debounce a function, so it will only be called after a certain amount of time has passed since the last call.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function debounce<C extends (...args: any[]) => unknown>(
    callback: C,
    delayDuration: number,
) {
    let timeout: ReturnType<typeof setTimeout>;

    return (...args: Parameters<C>) => {
        clearTimeout(timeout);

        timeout = setTimeout(() => callback(args), delayDuration);
    };
}
