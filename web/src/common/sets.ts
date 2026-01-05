/**
 * @file Set utilities.
 */

/**
 * Given a {@linkcode Set}, extract the type of its elements.
 */
export type UnwrapSet<T extends Set<unknown>> = T extends Set<infer U> ? U : never;
