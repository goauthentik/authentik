import * as crypto from "node:crypto";
import * as fs from "node:fs/promises";
import { join, relative } from "node:path";

import { ConsoleLogger } from "../../../packages/logger-js/lib/node.js";
import { $ } from "./commands.mjs";

const REGISTRY_URL = "https://registry.npmjs.org/corepack";
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
