/**
 * @file Locale manifest plugin for ESBuild.
 *
 * @import { BaseLogger } from "pino"
 * @import { Metafile, Plugin } from "esbuild"
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { ConsoleLogger } from "#logger/node";
import { DistDirectory } from "#paths/node";

const pluginName = "locale-manifest-plugin";

/**
 * The name of the manifest emitted into {@linkcode DistDirectory}.
 */
export const LocaleManifestFileName = "manifest.json";

/**
 * ESBuild reports each locale catalog as a dynamic-import chunk whose sole "own" input is
 * `src/locales/<tag>.ts`, i.e. the input identifies the chunk's language tag.
 */
const LocaleInputPattern = /(?:^|\/)src\/locales\/([^/]+)\.[cm]?[jt]s$/;

/**
 * Maps each locale tag to the `dist`-relative path of its catalog chunk.
 *
 * @param {Metafile} metafile
 * @returns {Record<string, string>}
 */
function createLocaleManifest(metafile) {
    /**
     * @type {Record<string, string>}
     */
    const manifest = {};

    for (const [outputPath, output] of Object.entries(metafile.outputs)) {
        if (!outputPath.endsWith(".js")) continue;

        for (const inputPath of Object.keys(output.inputs)) {
            const match = LocaleInputPattern.exec(inputPath);

            if (!match) continue;

            // Paths are stored relative to `dist` so the server can resolve them through
            // `{% static %}`, regardless of the directory the build ran in.
            const distIndex = outputPath.lastIndexOf("dist/");

            manifest[match[1]] =
                distIndex === -1 ? outputPath : outputPath.slice(distIndex + "dist/".length);

            break;
        }
    }

    return manifest;
}

/**
 * @typedef LocaleManifestPluginOptions
 *
 * @property {BaseLogger} [logger]
 */

/**
 * Emit a manifest mapping each locale tag to its content-hashed catalog chunk.
 *
 * The server reads the manifest to `modulepreload` the catalog for the request's locale,
 * so the chunk is fetched before the entry bundle boots, i.e. without a flash of
 * untranslated text.
 *
 * @param {LocaleManifestPluginOptions} [options]
 * @returns {Plugin}
 */
export function localeManifestPlugin({ logger = ConsoleLogger.child({ name: pluginName }) } = {}) {
    return {
        name: pluginName,
        setup(build) {
            build.initialOptions.metafile = true;

            build.onEnd(async ({ metafile }) => {
                if (!metafile) return;

                const manifest = createLocaleManifest(metafile);

                await fs.writeFile(
                    path.join(DistDirectory, LocaleManifestFileName),
                    JSON.stringify(manifest, null, 2),
                );

                logger.info(`Wrote locale manifest (${Object.keys(manifest).length} catalogs)`);
            });
        },
    };
}
