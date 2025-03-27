import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * @typedef {'@goauthentik/web'} WebPackageIdentifier
 */

/**
 * The root of the web package.
 */
export const PackageRoot = /** @type {WebPackageIdentifier} */ (resolve(__dirname));

/**
 * Path to the web package's distribution directory.
 *
 * This is where the built files are located after running the build process.
 */
export const DistDirectory = /** @type {`${WebPackageIdentifier}/dist`} */ (
    resolve(__dirname, "dist")
);
