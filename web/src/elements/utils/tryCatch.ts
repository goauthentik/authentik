type TryFn<T> = () => T;
type CatchFn<T> = (error: unknown) => T;

type TryCatchArgs<T> = {
    tryFn: TryFn<T>;
    catchFn: CatchFn<T>;
};

export function tryCatch<T>({ tryFn, catchFn }: TryCatchArgs<T>): T;
export function tryCatch<T>(tryFn: TryFn<T>, catchFn: CatchFn<T>): T;

const isTryCatchArgs = <T>(t: any): t is TryCatchArgs<T> =>
    typeof t === "object" && "tryFn" in t && "catchFn" in t;

export function tryCatch<T>(tryFn: TryFn<T> | TryCatchProps<T>, catchFn?: CatchFn<T>): T {
    if (isTryCatchArgs(tryFn)) {
        catchFn = tryFn.catchFn;
        tryFn = tryFn.tryFn;
    }

    if (catchFn === undefined) {
        catchFn = () => null;
    }

    try {
        return tryFn();
    } catch (error) {
        return catchFn(error);
    }
}
