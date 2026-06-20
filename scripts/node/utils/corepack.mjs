import * as crypto from "node:crypto";
import * as fs from "node:fs/promises";
import { join, relative } from "node:path";

import { ConsoleLogger } from "../../../packages/logger-js/lib/node.js";
import { $ } from "./commands.mjs";

const REGISTRY_BASE_URL = "https://registry.npmjs.org";
const REGISTRY_URL = `${REGISTRY_BASE_URL}/corepack`;
const OUTPUT_DIR = join(".corepack", "releases");
const OUTPUT_FILENAME = "latest.tgz";

export const corepack = $.bind("corepack");

/**
 * Reads the installed Corepack version.
 *
 * @param {string} [cwd] The directory to run the command in.
 * @returns {Promise<string | null>} The installed Corepack version
 */
export function readCorepackVersion(cwd = process.cwd()) {
    return $`corepack --version`({ cwd });
}

const logger = ConsoleLogger.prefix("setup-corepack");

/**
 * @param {string} baseDirectory
 */
export async function pullLatestCorepack(baseDirectory = process.cwd()) {
    logger.info("Fetching corepack metadata from registry...");

    const outputDir = join(baseDirectory, OUTPUT_DIR);
    const outputPath = join(outputDir, OUTPUT_FILENAME);

    const res = await fetch(REGISTRY_URL, { signal: AbortSignal.timeout(1000 * 60) });

    if (!res.ok) {
        throw new Error(`Failed to fetch registry metadata: ${res.status} ${res.statusText}`);
    }

    const metadata = await res.json();

    const latestVersion = metadata["dist-tags"].latest;
    const versionData = metadata.versions[latestVersion];
    const tarballUrl = versionData.dist.tarball;
    const expectedIntegrity = versionData.dist.integrity;

    logger.info(`Latest corepack version: ${latestVersion}`);
    logger.info(`Tarball URL: ${tarballUrl}`);
    logger.info(`Expected integrity: ${expectedIntegrity}`);

    logger.info({ url: tarballUrl }, "Downloading tarball...");

    const tarballRes = await fetch(tarballUrl, {
        signal: AbortSignal.timeout(1000 * 60),
    });

    if (!tarballRes.ok) {
        throw new Error(
            `Failed to download tarball: ${tarballRes.status} ${tarballRes.statusText}`,
        );
    }

    const tarballBuffer = Buffer.from(await tarballRes.arrayBuffer());

    logger.info("Verifying integrity...");

    const [algorithm, expectedHash] = expectedIntegrity.split("-");
    const actualHash = crypto.createHash(algorithm).update(tarballBuffer).digest("base64");

    if (actualHash !== expectedHash) {
        throw new Error(
            `Integrity mismatch!\n  Expected: ${expectedHash}\n  Actual:   ${actualHash}`,
        );
    }

    logger.info("Integrity verified.");

    await fs.mkdir(outputDir, { recursive: true });
    await fs.writeFile(outputPath, tarballBuffer);

    logger.info(`Saved to ${relative(baseDirectory, outputPath)}`);
    logger.info(`corepack@${latestVersion} (${expectedIntegrity})`);
}

/**
 * Downloads the tarball for a package manager spec from the npm registry and
 * verifies it matches the expected Corepack-style checksum (`<algorithm>.<hex>`).
 *
 * Corepack's CLI does not enforce the `+integrity` suffix on the `packageManager`
 * field when invoked via `corepack install -g`, so we verify the bytes ourselves
 * before handing control back to Corepack.
 *
 * @param {string} packageManager E.g. `npm@11.14.1`.
 * @param {string} expectedChecksum E.g. `sha512.6a8a4d67...`.
 * @returns {Promise<void>}
 */
export async function verifyPackageManagerIntegrity(packageManager, expectedChecksum) {
    const atIndex = packageManager.lastIndexOf("@");

    if (atIndex <= 0) {
        throw new Error(
            `Invalid packageManager spec "${packageManager}". Expected "name@version".`,
        );
    }

    const name = packageManager.slice(0, atIndex);
    const version = packageManager.slice(atIndex + 1);

    const separatorIndex = expectedChecksum.indexOf(".");

    if (separatorIndex <= 0) {
        throw new Error(
            `Invalid checksum format "${expectedChecksum}". Expected "<algorithm>.<hex>".`,
        );
    }

    const algorithm = expectedChecksum.slice(0, separatorIndex);
    const expectedHex = expectedChecksum.slice(separatorIndex + 1).toLowerCase();

    logger.info(`Verifying ${name}@${version} against ${algorithm} checksum...`);

    const metadataUrl = `${REGISTRY_BASE_URL}/${encodeURIComponent(name)}/${encodeURIComponent(version)}`;

    const metadataRes = await fetch(metadataUrl, {
        signal: AbortSignal.timeout(1000 * 60),
    });

    if (!metadataRes.ok) {
        throw new Error(
            `Failed to fetch registry metadata for ${name}@${version}: ${metadataRes.status} ${metadataRes.statusText}`,
        );
    }

    const versionData = await metadataRes.json();
    const tarballUrl = versionData?.dist?.tarball;

    if (!tarballUrl) {
        throw new Error(`Registry response missing dist.tarball for ${name}@${version}.`);
    }

    logger.info({ url: tarballUrl }, "Downloading tarball...");

    const tarballRes = await fetch(tarballUrl, {
        signal: AbortSignal.timeout(1000 * 60),
    });

    if (!tarballRes.ok) {
        throw new Error(
            `Failed to download tarball: ${tarballRes.status} ${tarballRes.statusText}`,
        );
    }

    const tarballBuffer = Buffer.from(await tarballRes.arrayBuffer());
    const actualHex = crypto.createHash(algorithm).update(tarballBuffer).digest("hex");

    if (actualHex !== expectedHex) {
        throw new Error(
            `Integrity mismatch for ${name}@${version}!\n  Expected: ${algorithm}.${expectedHex}\n  Actual:   ${algorithm}.${actualHex}`,
        );
    }

    logger.info(`Integrity verified for ${name}@${version}.`);
}
