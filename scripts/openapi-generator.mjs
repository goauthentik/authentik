/**
 * @file OpenAPI generator utilities.
 */
import { execFileSync, execSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { userInfo } from "node:os";
import { join, relative, resolve } from "node:path";

const OPENAPI_CONTAINER_IMAGE = "docker.io/openapitools/openapi-generator-cli:v7.11.0";

/**
 * Checks if a command exists in the PATH.
 *
 * @template {string} T
 * @param {T} command
 * @returns {T | null}
 */
function commandExists(command) {
    if (execSync(`command -v ${command} || echo ''`).toString().trim()) {
        return command;
    }

    return null;
}

/**
 * Given a path relative to the current working directory,
 * resolves it to a path relative to the local volume.
 *
 * @param {string} cwd
 * @param {...string} pathSegments
 */
function resolveLocalPath(cwd, ...pathSegments) {
    return resolve("/local", relative(cwd, join(...pathSegments)));
}

/**
 * @typedef {object} GenerateOpenAPIClientOptions
 * @property {string} cwd The working directory to run the generator in.
 * @property {string} outputDirectory The path to the output directory.
 * @property {string} generatorName The name of the generator.
 * @property {string} config The path to the generator configuration.
 * @property {string} [inputSpec] The path to the OpenAPI specification.
 * @property {Array<string | string[]>} [commandArgs] Additional arguments to pass to the generator.
 */

/**
 * Generates an OpenAPI client using the `openapi-generator-cli` Docker image.
 *
 * @param {GenerateOpenAPIClientOptions} options
 * @see {@link https://openapi-generator.tech/docs/usage}
 */
export function generateOpenAPIClient({
    cwd,
    outputDirectory,
    generatorName,
    config,
    inputSpec = resolve(cwd, "schema.yml"),
    commandArgs = [],
}) {
    if (existsSync(outputDirectory)) {
        console.log(`Removing existing generated API client from ${outputDirectory}`);

        rmSync(outputDirectory, { recursive: true, force: true });
    }

    const containerEngine = commandExists("docker") || commandExists("podman");

    if (!containerEngine) {
        throw new Error("Container engine not found. Is Docker or Podman available in the PATH?");
    }

    const { gid, uid } = userInfo();

    const args = [
        "run",
        [`--user`, `${uid}:${gid}`],
        `--rm`,
        [`-v`, `${cwd}:/local`],
        OPENAPI_CONTAINER_IMAGE,
        "generate",
        ["--input-spec", resolveLocalPath(cwd, inputSpec)],
        [`--generator-name`, generatorName],
        ["--config", resolveLocalPath(cwd, config)],
        ["--git-repo-id", `authentik`],
        ["--git-user-id", `goauthentik`],
        ["--output", resolveLocalPath(cwd, outputDirectory)],

        ...commandArgs,
    ];

    console.debug(`Running command: ${containerEngine}`, args);

    execFileSync(containerEngine, args.flat(), {
        cwd,
        stdio: "inherit",
    });

    console.log(`Generated API client to ${outputDirectory}`);
}
