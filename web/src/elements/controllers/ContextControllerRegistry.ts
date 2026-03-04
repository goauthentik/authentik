import { type ContextControllerRegistryMap } from "#elements/types";

/**
 * A registry of context controllers added to the Interface.
 *
 * @singleton
 *
 * @remarks
 *
 * This is exported separately to avoid circular dependencies.
 */
export const ContextControllerRegistry = new WeakMap() as ContextControllerRegistryMap;
