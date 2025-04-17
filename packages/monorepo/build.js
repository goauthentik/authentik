/**
 * @file Utility functions for building and copying files.
 */

/**
 * Given an object of environment variables, returns a new object with the same keys and values, but
 * with the values serialized as strings.
 * @template {string} K
 *
 * @param {Record<K, string | number | boolean | object>} input
 * @returns {Record<`process.env.${K}`, string>}
 */
export function serializeEnvironmentVars(input) {
    /**
     * @type {Record<string, string>}
     */
    const env = {};

    for (const [key, value] of Object.entries(input)) {
        const namespaceKey = `process.env.${key}`;
        env[namespaceKey] = JSON.stringify(value || "");
    }

    return /** @type {Record<string, string>} */ (env);
}
