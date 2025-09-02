/**
 * @file Utility functions for working with semantic versions.
 *
 * @runtime node
 */
import { MonoRepoRoot } from "#paths/node";
import { execSync } from "node:child_process";

// ts-import-sorter: disable
import PackageJSON from "../../../../package.json" with { type: "json" };

/**
 * The current version of authentik in SemVer format.
 *
 * @runtime node
 */
export const AuthentikVersion = /**@type {`${number}.${number}.${number}`} */ (PackageJSON.version);

/**
 * Reads the last commit hash from the current git repository.
 *
 * @runtime node
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
 * This must match the behavior defined in authentik's server-side `authentik_full_version` function.
 *
 * @runtime node
 * @see {@link "authentik\_\_init\_\_.py"}
 */
export function readBuildIdentifier() {
    const { GIT_BUILD_HASH } = process.env;

    if (!GIT_BUILD_HASH) {
        console.warn("GIT_BUILD_HASH is not set, falling back to authentik version.");
        return AuthentikVersion;
    }

    return [AuthentikVersion, GIT_BUILD_HASH].join("+");
}
