#!/usr/bin/env node
/**
 * @file Generates the authentik API client for TypeScript.
 */
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import PackageJSON from "../package.json" with { type: "json" };
import { generateOpenAPIClient } from "./openapi-generator.mjs";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));

const repoRoot = resolve(scriptDirectory, "..");
const npmVersion = [PackageJSON.version, Date.now()].join("-");

generateOpenAPIClient({
    cwd: repoRoot,
    outputDirectory: resolve(repoRoot, "gen-ts-api"),
    generatorName: "typescript-fetch",
    config: resolve(scriptDirectory, "api-ts-config.yaml"),
    commandArgs: [`--additional-properties=npmVersion=${npmVersion}`],
});
