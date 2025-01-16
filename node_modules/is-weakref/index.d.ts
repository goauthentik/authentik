declare function isWeakRef<T extends object>(value: unknown): value is WeakRef<T>;

export = isWeakRef;