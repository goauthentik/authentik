/**
 * @file Utility functions for working with environment variables.
 */
/// <reference types="../types/node.js" />

//#region Constants

/**
 * The current Node.js environment, defaulting to "development" when not set.
 *
 * Note, this should only be used during the build process.
 *
 * If you need to check the environment at runtime, use `process.env.NODE_ENV` to
 * ensure that module tree-shaking works correctly.
 *
 * @category Environment
 * @runtime node
 */
export const NodeEnvironment = process.env.NODE_ENV || "development";

/**
 * A source environment variable, which can be a string, number, boolean, null, or undefined.
 * @typedef {string | number | boolean | null | undefined} EnvironmentVariable
 */

/**
 * A type helper for serializing environment variables.
 *
 * @category Environment
 * @template {EnvironmentVariable} T
 * @typedef {T extends string ? `"${T}"` : T} JSONify
 */

//#endregion

//#region Utilities

/**
 * Given an object of environment variables, serializes them into a mapping of
 * environment variable names to their respective runtime constants.
 *
 * This is useful for defining environment variables while bundling with ESBuild, Vite, etc.
 *
 * @category Environment
 * @runtime node
 *
 * @template {Record<string, EnvironmentVariable>} EnvRecord
 * @template {string} [Prefix='import.meta.env.']
 *
 * @param {EnvRecord} input
 * @param {Prefix} [prefix='import.meta.env.']
 *
 * @returns {{[K in keyof EnvRecord as `${Prefix}${K}`]: JSONify<EnvRecord[K]>}}
 */
export function serializeEnvironmentVars(
    input,
    prefix = /** @type {Prefix} */ ("import.meta.env."),
) {
    const env = Object.fromEntries(
        Object.entries(input).map(([key, value]) => [prefix + key, JSON.stringify(value ?? "")]),
    );

    return /** @type {any} */ (env);
}

//#endregion
