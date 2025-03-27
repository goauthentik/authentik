import { execSync } from "node:child_process";

import PackageJSON from "../../package.json" with { type: "json" };
import { MonoRepoRoot } from "./paths.js";

/**
 * The current version of authentik in SemVer format.
 *
 */
export const AuthentikVersion = /**@type {`${number}.${number}.${number}`} */ (PackageJSON.version);

/**
 * Reads the last commit hash from the current git repository.
 */
export function readGitBuildHash() {
    try {
        const commit = execSync("git rev-parse HEAD", {
            encoding: "utf8",
            cwd: MonoRepoRoot,
        })
            .toString()
            .trim();

        return commit;
    } catch (_error) {
        console.debug("Git commit could not be read.");
    }

    return process.env.GIT_BUILD_HASH || "";
}

/**
 * Reads the build identifier for the current environment.
 *
 * This must match the behavior defined in authentik's server-side `get_full_version` function.
 *
 * @see {@link "authentik\_\_init\_\_.py"}
 */
export function readBuildIdentifier() {
    const { GIT_BUILD_HASH = "d72def036820985a909266e8167ccb8087c7ce32" } = process.env;

    if (!GIT_BUILD_HASH) return AuthentikVersion;

    return [AuthentikVersion, GIT_BUILD_HASH].join("+");
}
