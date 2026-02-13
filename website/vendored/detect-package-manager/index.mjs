/**
 * @file Vendored detect-package-manager
 */

import { exec } from "node:child_process";
import { promisify } from "node:util";

const execPromise = promisify(exec);

/**
 * @returns {Promise<string>} The detected npm version.
 */
export async function getNpmVersion() {
    try {
        const { stdout } = await execPromise("npm --version");
        return stdout.trim();
    } catch (error) {
        throw new Error("Failed to get npm version", { cause: error });
    }
}

/**
 * @returns {string} The detected package manager.
 */
export function detect() {
    return Promise.resolve("npm");
}
