/**
 * @file Paths used by the web package.
 *
 * @runtime node
 */

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { DistDirectoryName } from "#paths";

const relativeDirname = dirname(fileURLToPath(import.meta.url));

//#region Base paths

export type WebPackageIdentifier = "@goauthentik/web";

/**
 * The root of the web package.
 *
 * @runtime node
 */
export const PackageRoot = resolve(relativeDirname, "..") as WebPackageIdentifier;

/**
 * Path to the web package's distribution directory.
 *
 * This is where the built files are located after running the build process.
 *
 * @runtime node
 */
export const DistDirectory = resolve(
    PackageRoot,
    DistDirectoryName,
) as `${WebPackageIdentifier}/${typeof DistDirectoryName}`;

//#endregion

//#region Entry points

/**
 * ESBuild entrypoint target.
 *
 * Matches the type defined in the ESBuild context.
 */
export interface EntryPointTarget {
    in: string;
    out: string;
}

/**
 * Entry points available for building.
 *
 * @runtime node
 */
export const EntryPoint = {
    Admin: {
        in: resolve(PackageRoot, "src", "admin", "index.entrypoint.ts"),
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
    InterfaceStyles: {
        in: resolve(PackageRoot, "src", "styles", "interface.global.css"),
        out: resolve(DistDirectory, "styles", "interface"),
    },
    StaticStyles: {
        in: resolve(PackageRoot, "src", "styles", "static.global.css"),
        out: resolve(DistDirectory, "styles", "static"),
    },
    FlowStyles: {
        in: resolve(PackageRoot, "src", "styles", "flows.global.css"),
        out: resolve(DistDirectory, "styles", "flow"),
    },
} as const satisfies Record<string, EntryPointTarget>;

//#endregion
