/** Share a request while it is in flight, and allow retries as soon as it settles. */
export function singleFlight<TKey, TResult>(
    send: (key: TKey) => Promise<TResult>,
): (key: TKey) => Promise<TResult> {
    const pending = new Map<TKey, Promise<TResult>>();

    return (key) => {
        const existing = pending.get(key);

        if (existing) {
            return existing;
        }

        const request = Promise.resolve()
            .then(() => send(key))
            .finally(() => pending.delete(key));

        pending.set(key, request);

        return request;
    };
}
