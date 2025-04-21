/**
 * @file Utility functions for building and copying files.
 */

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
 * Given an object of environment variables, returns a new object with the same keys and values, but
 * with the values serialized as strings.
 *
 * @template {Record<string, EnvironmentVariable>} EnvRecord
 * @template {string} [Prefix='process.env.']
 *
 * @param {EnvRecord} input
 * @param {Prefix} [prefix='process.env.']
 *
 * @returns {{[K in keyof EnvRecord as `${Prefix}${K}`]: JSONify<EnvRecord[K]>}}
 */
export function serializeEnvironmentVars(input, prefix = /** @type {Prefix} */ ("process.env.")) {
    /**
     * @type {Record<string, string>}
     */
    const env = {};

    for (const [key, value] of Object.entries(input)) {
        const namespaceKey = prefix + key;

        env[namespaceKey] = JSON.stringify(value || "");
    }

    return /** @type {any} */ (env);
}
