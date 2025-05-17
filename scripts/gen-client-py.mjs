#!/usr/bin/env node
/**
 * @file Generates the authentik API client for Python.
 */
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { generateOpenAPIClient } from "./openapi-generator.mjs";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));

const repoRoot = resolve(scriptDirectory, "..");

generateOpenAPIClient({
    cwd: repoRoot,
    outputDirectory: resolve(repoRoot, "gen-py-api"),
    generatorName: "python",
    config: resolve(scriptDirectory, "api-py-config.yaml"),
});
