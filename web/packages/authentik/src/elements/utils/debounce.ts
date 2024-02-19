// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Callback = (...args: any[]) => any;
export function debounce<F extends Callback, T extends object>(callback: F, wait: number) {
    let timeout: ReturnType<typeof setTimeout>;
    return (...args: Parameters<F>) => {
        // @ts-ignore
        const context: T = this satisfies object;
        if (timeout !== undefined) {
            clearTimeout(timeout);
        }
        timeout = setTimeout(() => callback.apply(context, args), wait);
    };
}
