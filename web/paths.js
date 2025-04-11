import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

//#region Base paths

/**
 * @typedef {'@goauthentik/web'} WebPackageIdentifier
 */

/**
 * The root of the web package.
 */
export const PackageRoot = /** @type {WebPackageIdentifier} */ (resolve(__dirname));

/**
 * The name of the distribution directory.
 */
export const DistDirectoryName = "dist";

/**
 * Path to the web package's distribution directory.
 *
 * This is where the built files are located after running the build process.
 */
export const DistDirectory = /** @type {`${WebPackageIdentifier}/${DistDirectoryName}`} */ (
    resolve(__dirname, DistDirectoryName)
);

//#endregion

//#region Entry points

/**
 * @typedef {{ in: string, out: string }} EntryPointTarget
 *
 * ESBuild entrypoint target.
 * Matches the type defined in the ESBuild context.
 */

/**
 * Entry points available for building.
 *
 * @satisfies {Record<string, EntryPointTarget>}
 */
export const EntryPoint = /** @type {const} */ ({
    Admin: {
        in: resolve(PackageRoot, "src", "admin", "AdminInterface", "AdminInterface.ts"),
        out: resolve(DistDirectory, "admin", "AdminInterface"),
    },
    User: {
        in: resolve(PackageRoot, "src", "user", "UserInterface.ts"),
        out: resolve(DistDirectory, "user", "UserInterface"),
    },
    Flow: {
        in: resolve(PackageRoot, "src", "flow", "FlowInterface.ts"),
        out: resolve(DistDirectory, "flow", "FlowInterface"),
    },
    Standalone: {
        in: resolve(PackageRoot, "src", "standalone", "api-browser/index.ts"),
        out: resolve(DistDirectory, "standalone", "api-browser", "index"),
    },
    StandaloneLoading: {
        in: resolve(PackageRoot, "src", "standalone", "loading/index.ts"),
        out: resolve(DistDirectory, "standalone", "loading", "index"),
    },
    RAC: {
        in: resolve(PackageRoot, "src", "rac", "index.ts"),
        out: resolve(DistDirectory, "rac", "index"),
    },
    Polyfill: {
        in: resolve(PackageRoot, "src", "polyfill", "poly.ts"),
        out: resolve(DistDirectory, "poly"),
    },
});

//#endregion
