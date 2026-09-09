/**
 * @file Type utilities for ESM modules.
 */

/**
 * A type representing a resolved ES module with a default export of type `DefaultExport`.
 *
 * ```ts
 * const mod: ResolvedESModule<MyType> = await import('./my-module.js');
 * const myValue: MyType = mod.default;
 * ```
 */
export interface ResolvedDefaultESModule<DefaultExport> {
    default: DefaultExport;
}

/**
 * A callback that returns a promise resolving to a module of type `T`.
 */
export type ImportCallback<T extends object> = () => Promise<T>;

/**
 * A callback that returns a promise resolving to a module with a default export of type `T`.
 */
export type DefaultImportCallback<T = unknown> = ImportCallback<ResolvedDefaultESModule<T>>;

/**
 * Asserts that the given module has a default export and is an object.
 *
 * @param mod The module to check.
 * @throws {TypeError} If the module is not an object or does not have a default export.
 */
export function assertDefaultExport<T>(mod: unknown): asserts mod is ResolvedDefaultESModule<T> {
    if (!mod || typeof mod !== "object") {
        throw new TypeError("Module is not an object");
    }

    if (!Object.hasOwn(mod, "default")) {
        throw new TypeError("Module does not have a default export");
    }
}
