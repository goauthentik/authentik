import { type ContextControllerRegistryMap } from "#elements/types";

/**
 * Check if the environment supports Symbol-keyed WeakMaps.
 *
 * @see {@link https://caniuse.com/mdn-javascript_builtins_weakmap_symbol_as_keys | Can I use}
 *
 * @todo Re-evaluate browser coverage after 2027-01-01
 */
function supportsSymbolKeyedWeakMap(): boolean {
    const testKey = Symbol("test");
    const wm = new WeakMap();

    try {
        wm.set(testKey, "value");
        return wm.has(testKey);
    } catch (_error) {
        return false;
    }
}

/**
 * A constructor for either WeakMap or Map, depending on environment support.
 *
 * @remarks
 *
 * A preference for `WeakMap` is optional at the moment.
 * However, if we ever support short-lived context controllers, such as
 */
const ContextControllerConstructor = supportsSymbolKeyedWeakMap() ? WeakMap : Map;

/**
 * A registry of context controllers added to the Interface.
 *
 * @singleton
 *
 * @remarks
 *
 * This is exported separately to avoid circular dependencies.
 */
export const ContextControllerRegistry =
    new ContextControllerConstructor() as ContextControllerRegistryMap;
