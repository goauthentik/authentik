/******************************************************************************
 * Copyright 2023 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { Disposable } from './disposable.js';
import type { URI } from './uri-utils.js';
import type { LangiumSharedCoreServices } from '../services.js';
export declare abstract class DisposableCache implements Disposable {
    protected toDispose: Disposable[];
    protected isDisposed: boolean;
    onDispose(disposable: Disposable): void;
    dispose(): void;
    protected throwIfDisposed(): void;
    abstract clear(): void;
}
export declare class SimpleCache<K, V> extends DisposableCache {
    protected readonly cache: Map<K, V>;
    has(key: K): boolean;
    set(key: K, value: V): void;
    get(key: K): V | undefined;
    get(key: K, provider: () => V): V;
    delete(key: K): boolean;
    clear(): void;
}
export declare class ContextCache<Context, Key, Value, ContextKey = Context> extends DisposableCache {
    private readonly cache;
    private readonly converter;
    constructor(converter?: (input: Context) => ContextKey);
    has(contextKey: Context, key: Key): boolean;
    set(contextKey: Context, key: Key, value: Value): void;
    get(contextKey: Context, key: Key): Value | undefined;
    get(contextKey: Context, key: Key, provider: () => Value): Value;
    delete(contextKey: Context, key: Key): boolean;
    clear(): void;
    clear(contextKey: Context): void;
    protected cacheForContext(contextKey: Context): Map<Key, Value>;
}
/**
 * Every key/value pair in this cache is scoped to a document.
 * If this document is changed or deleted, all associated key/value pairs are deleted.
 */
export declare class DocumentCache<K, V> extends ContextCache<URI | string, K, V, string> {
    constructor(sharedServices: LangiumSharedCoreServices);
}
/**
 * Every key/value pair in this cache is scoped to the whole workspace.
 * If any document in the workspace changes, the whole cache is evicted.
 */
export declare class WorkspaceCache<K, V> extends SimpleCache<K, V> {
    constructor(sharedServices: LangiumSharedCoreServices);
}
//# sourceMappingURL=caching.d.ts.map