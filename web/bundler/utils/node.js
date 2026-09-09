/**
 * @file Bundler utilities.
 */

import { NodeEnvironment, serializeEnvironmentVars } from "@goauthentik/core/environment/node";
import {
    AuthentikVersion,
    CurrentReleaseDocsURL,
    PreReleaseDocsURL,
    ReleaseNotesURL,
} from "@goauthentik/core/version/node";

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
        AK_VERSION: AuthentikVersion,
        AK_DOCS_URL: CurrentReleaseDocsURL.href,
        AK_DOCS_RELEASE_NOTES_URL: ReleaseNotesURL.href,
        AK_DOCS_PRE_RELEASE_URL: PreReleaseDocsURL.href,
        AK_API_BASE_PATH: process.env.AK_API_BASE_PATH ?? "",
        AK_BUNDLER: JSON.stringify(process.env.AK_BUNDLER ?? "authentik"),
    };

    return {
        ...serializeEnvironmentVars(envRecord),
        // We need to explicitly set this for NPM packages that use `process`
        // to determine their environment.
        "process.env.NODE_ENV": SerializedNodeEnvironment,
    };
}
