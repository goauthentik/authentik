type TryFn<T> = () => T;
type CatchFn<T> = (error: unknown) => T;

type TryCatchArgs<T> = {
    tryFn: TryFn<T>;
    catchFn?: CatchFn<T>;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isTryCatchArgs = <T>(t: any): t is TryCatchArgs<T> =>
    typeof t === "object" && "tryFn" in t && "catchFn" in t;

export function tryCatch<T>({ tryFn, catchFn }: TryCatchArgs<T>): T;
export function tryCatch<T>(tryFn: TryFn<T>): T;
export function tryCatch<T>(tryFn: TryFn<T>, catchFn: CatchFn<T>): T;
export function tryCatch<T>(tryFn: TryFn<T> | TryCatchArgs<T>, catchFn?: CatchFn<T>): T {
    if (isTryCatchArgs(tryFn)) {
        catchFn = tryFn.catchFn;
        tryFn = tryFn.tryFn;
    }

    if (catchFn === undefined) {
        catchFn = () => null as T;
    }

    try {
        return tryFn();
    } catch (error) {
        return catchFn(error);
    }
}
