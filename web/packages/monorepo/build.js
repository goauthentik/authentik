/**
 * @file Utility functions for building and copying files.
 */
import { NodeEnvironment } from "./constants.js";

/**
 * A source environment variable, which can be a string, number, boolean, null, or undefined.
 * @typedef {string | number | boolean | null | undefined} EnvironmentVariable
 */

/**
 * A type helper for serializing environment variables.
 *
 * @template {EnvironmentVariable} T
 * @typedef {T extends string ? `"${T}"` : T} JSONify
 */

/**
 * @typedef {{
 * "process.env.NODE_ENV": `"development"` | `"production"`
 * }} SerializedNodeEnvironment
 */

/**
 * Given an object of environment variables, returns a new object with the same keys and values, but
 * with the values serialized as strings.
 *
 * @template {Record<string, EnvironmentVariable>} EnvRecord
 * @template {string} [Prefix='import.meta.env.']
 *
 * @param {EnvRecord} input
 * @param {Prefix} [prefix='import.meta.env.']
 *
 * @returns {SerializedNodeEnvironment & {[K in keyof EnvRecord as `${Prefix}${K}`]: JSONify<EnvRecord[K]>}}
 */
export function serializeEnvironmentVars(
    input,
    prefix = /** @type {Prefix} */ ("import.meta.env."),
) {
    /**
     * @type {Record<string, string>}
     */
    const env = {
        // We need to explicitly set this for NPM packages that use `process`
        // to determine their environment.
        "process.env.NODE_ENV": JSON.stringify(NodeEnvironment),
    };

    for (const [key, value] of Object.entries(input)) {
        const namespaceKey = prefix + key;

        env[namespaceKey] = JSON.stringify(value || "");
    }

    return /** @type {any} */ (env);
}
