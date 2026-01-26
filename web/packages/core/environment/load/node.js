/**
 * @file Load the contents of an environment file into `process.env`.
 */

import { existsSync } from "node:fs";
import { join } from "node:path";

import { MonoRepoRoot } from "#paths/node";

const envFilePath = join(MonoRepoRoot, ".env");

if (existsSync(envFilePath)) {
    console.debug(`Loading environment from ${envFilePath}`);

    try {
        process.loadEnvFile(envFilePath);
    } catch (error) {
        console.warn(`Failed to load environment from ${envFilePath}:`, error);
    }
}
