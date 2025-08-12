/**
 * @file Bundler utilities.
 */

import { NodeEnvironment, serializeEnvironmentVars } from "@goauthentik/core/environment/node";
import { readAuthentikVersion } from "@goauthentik/core/version/node";

/**
 * Creates a mapping of environment variables to their respective runtime constants.
 */
export function createBundleDefinitions() {
    const SerializedNodeEnvironment = /** @type {`"development"` | `"production"`} */ (
        JSON.stringify(NodeEnvironment)
    );

    /**
     * @satisfies {Record<ESBuildImportEnvKey, string>}
     */
    const envRecord = {
        AK_VERSION: readAuthentikVersion(),
        AK_API_BASE_PATH: process.env.AK_API_BASE_PATH ?? "",
    };

    return {
        ...serializeEnvironmentVars(envRecord),
        // We need to explicitly set this for NPM packages that use `process`
        // to determine their environment.
        "process.env.NODE_ENV": SerializedNodeEnvironment,
    };
}
