/**
 * @file Paths used by the web package.
 *
 * @runtime node
 */

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { DistDirectoryName } from "#paths";

import { resolvePackage } from "@goauthentik/core/paths/node";

const relativeDirname = dirname(fileURLToPath(import.meta.url));

//#region Base paths

/**
 * @typedef {'@goauthentik/web'} WebPackageIdentifier
 */

/**
 * The root of the web package.
 *
 * @runtime node
 */
export const PackageRoot = /** @type {WebPackageIdentifier} */ (resolve(relativeDirname, ".."));

/**
 * Path to the web package's distribution directory.
 *
 * This is where the built files are located after running the build process.
 *
 * @runtime node
 */
export const DistDirectory = /** @type {`${WebPackageIdentifier}/${DistDirectoryName}`} */ (
    resolve(PackageRoot, DistDirectoryName)
);

//#endregion

//#region Entry points

/**
 * @typedef {{ in: string, out: string }} EntryPointTarget
 *
 * ESBuild entrypoint target.
 * Matches the type defined in the ESBuild context.
 */

const patternflyPath = resolvePackage("@patternfly/patternfly", import.meta);

/**
 * Entry points available for building.
 *
 * @satisfies {Record<string, EntryPointTarget>}
 *
 * @runtime node
 */
export const EntryPoint = /** @type {const} */ ({
    Admin: {
        in: resolve(PackageRoot, "src", "admin", "AdminInterface", "index.entrypoint.ts"),
        out: resolve(DistDirectory, "admin", "AdminInterface"),
    },
    User: {
        in: resolve(PackageRoot, "src", "user", "index.entrypoint.ts"),
        out: resolve(DistDirectory, "user", "UserInterface"),
    },
    Flow: {
        in: resolve(PackageRoot, "src", "flow", "index.entrypoint.ts"),
        out: resolve(DistDirectory, "flow", "FlowInterface"),
    },
    StandaloneAPI: {
        in: resolve(PackageRoot, "src", "standalone", "api-browser/index.entrypoint.ts"),
        out: resolve(DistDirectory, "standalone", "api-browser", "index"),
    },
    StandaloneLoading: {
        in: resolve(PackageRoot, "src", "standalone", "loading/index.entrypoint.ts"),
        out: resolve(DistDirectory, "standalone", "loading", "index"),
    },
    RAC: {
        in: resolve(PackageRoot, "src", "rac", "index.entrypoint.ts"),
        out: resolve(DistDirectory, "rac", "index"),
    },
    Polyfill: {
        in: resolve(PackageRoot, "src", "polyfill", "index.entrypoint.ts"),
        out: resolve(DistDirectory, "poly"),
    },
    ThemeBase: {
        in: resolve(PackageRoot, "src", "common", "styles", "base.global.css"),
        out: resolve(DistDirectory, "styles", "base"),
    },
    ThemeDark: {
        in: resolve(PackageRoot, "src", "common", "styles", "dark.global.css"),
        out: resolve(DistDirectory, "styles", "dark"),
    },
});

//#endregion
