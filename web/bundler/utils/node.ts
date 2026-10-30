/**
 * @file Bundler utilities.
 */

import { createRequire } from "node:module";
import { dirname, join } from "node:path";

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
    const SerializedNodeEnvironment = JSON.stringify(NodeEnvironment) as
        | `"development"`
        | `"production"`;

    const envRecord = {
        AK_VERSION: AuthentikVersion,
        AK_DOCS_URL: CurrentReleaseDocsURL.href,
        AK_DOCS_RELEASE_NOTES_URL: ReleaseNotesURL.href,
        AK_DOCS_PRE_RELEASE_URL: PreReleaseDocsURL.href,
        AK_API_BASE_PATH: process.env.AK_API_BASE_PATH ?? "",
        AK_BUNDLER: JSON.stringify(process.env.AK_BUNDLER ?? "authentik"),
    } satisfies Record<ESBuildImportEnvKey, string>;

    return {
        ...serializeEnvironmentVars(envRecord),
        // We need to explicitly set this for NPM packages that use `process`
        // to determine their environment.
        "process.env.NODE_ENV": SerializedNodeEnvironment,
    };
}

/**
 * Creates a mapping of import paths to the files a package ships without exporting them.
 */
export function createBundleAliases(): Record<string, string> {
    const require = createRequire(import.meta.url);

    return {
        // Monaco's `exports` map covers only its modules. The editor renders in a shadow root,
        // so it needs the stylesheet that its modules would otherwise inject into the document.
        // `require` resolves the package to `min/vs/index.js`, next to that stylesheet.
        "monaco-editor/min/vs/editor/editor.main.css": join(
            dirname(require.resolve("monaco-editor")),
            "editor",
            "editor.main.css",
        ),
    };
}
