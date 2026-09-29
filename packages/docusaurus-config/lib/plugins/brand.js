/**
 * @import { Plugin } from "@docusaurus/types";
 * @file Docusaurus plugin copying authentik's brand assets into a site's static directory.
 */

import { cp, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";

const require = createRequire(import.meta.url);

const SourcePackage = "@goauthentik/brand-assets";

/**
 * A tuple representing a source file and its destination path within the static directory.
 *
 * @typedef {[source: string, destination: string]} AssetEntry
 */

/**
 * Files within {@linkcode SourcePackage}, paired with their destination
 * in the root static directory.
 *
 * Lockup names are intentionally swapped so `icon_left_brand.svg` is white by default.
 *
 * @type {ReadonlyArray<AssetEntry>}
 */
const BrandAssets = [
    ["icon.png", "img/icon.png"],
    ["icon.svg", "img/icon.svg"],
    ["social.png", "img/social.png"],
    // cspell:disable-next-line
    ["icon_left_brand.svg", "img/icon_left_brand_colour.svg"],
    ["icon_left_brand_white.svg", "img/icon_left_brand.svg"],
    // cspell:disable-next-line
    ["icon_top_brand.svg", "img/icon_top_brand_colour.svg"],
    ["icon_top_brand_white.svg", "img/icon_top_brand.svg"],
];

/**
 * @typedef BrandAssetsPluginOptions
 * @property {string} rootStaticDirectory Static directory receiving {@linkcode BrandAssets},
 * @property {string} [packageStaticDirectory] Static directory receiving
 *   {@linkcode BrandAssetsPluginOptions.additionalAssets}. Defaults to `rootStaticDirectory`.
 * @property {Iterable<AssetEntry>} [additionalAssets] Site-owned assets to copy alongside the
 *   brand assets. Each source is an absolute path or a specifier resolved from the site.
 */

/**
 * Docusaurus plugin for copying authentik's brand assets into a site's static directory.
 *
 * @param {{ siteDir: string }} context
 * @param {BrandAssetsPluginOptions} options
 *
 * @returns {Plugin<unknown>}
 */
export default function brandAssets(
    { siteDir },
    { rootStaticDirectory, packageStaticDirectory = rootStaticDirectory, additionalAssets = [] },
) {
    const siteRequire = createRequire(join(siteDir, "package.json"));

    /**
     * @type {ReadonlyArray<AssetEntry>}
     */
    const resolvedEntries = [
        ...BrandAssets.map(([source, destination]) => /** @type {AssetEntry} */ ([
            require.resolve(`${SourcePackage}/${source}`),
            resolve(rootStaticDirectory, destination),
        ])),
        ...Array.from(additionalAssets, ([source, destination]) => /** @type {AssetEntry} */ ([
            siteRequire.resolve(source),
            resolve(packageStaticDirectory, destination),
        ])),
    ];

    const loadContent = async () => {
        await Promise.all(
            resolvedEntries.map(async ([sourcePath, destinationPath]) => {
                await mkdir(dirname(destinationPath), { recursive: true });

                return cp(sourcePath, destinationPath, { recursive: true });
            }),
        );
    };

    return {
        name: "authentik-brand-assets",
        loadContent,
    };
}

/**
 * @param {BrandAssetsPluginOptions} options
 *
 * @returns {[string, BrandAssetsPluginOptions]}
 */
export function brandAssetsPlugin(options) {
    return ["@goauthentik/docusaurus-config/plugins/brand", options];
}
