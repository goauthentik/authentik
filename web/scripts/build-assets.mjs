import "@goauthentik/core/environment/load/node";
import * as fs from "node:fs/promises";
import { createRequire } from "node:module";
import * as path from "node:path";

import { ConsoleLogger } from "#logger/node";
import { DistDirectory, EntryPoint, PackageRoot } from "#paths/node";

const require = createRequire(import.meta.url);
const logger = ConsoleLogger.child({ name: "Assets" });

/**
 * @typedef {[from: string, to: string]} SourceDestinationPair
 */

/**
 * @type {SourceDestinationPair[]}
 */
const assets = [
    [
        path.join(path.dirname(EntryPoint.StandaloneLoading.in), "startup"),
        path.dirname(EntryPoint.StandaloneLoading.out),
    ],
    [path.resolve(PackageRoot, "src", "assets", "images"), "./assets/images"],
    [require.resolve("@goauthentik/brand-assets/brand.png"), "./assets/icons/brand.png"],
    [require.resolve("@goauthentik/brand-assets/brand.svg"), "./assets/icons/brand.svg"],
    [require.resolve("@goauthentik/brand-assets/icon.png"), "./assets/icons/icon.png"],
    [require.resolve("@goauthentik/brand-assets/icon.svg"), "./assets/icons/icon.svg"],
    [
        require.resolve("@goauthentik/brand-assets/icon_left_brand.png"),
        "./assets/icons/icon_left_brand.png",
    ],
    [
        require.resolve("@goauthentik/brand-assets/icon_left_brand.svg"),
        "./assets/icons/icon_left_brand.svg",
    ],
    [
        require.resolve("@goauthentik/brand-assets/icon_pride_lgbt.png"),
        "./assets/icons/icon_pride_lgbt.png",
    ],
    [
        require.resolve("@goauthentik/brand-assets/icon_pride_trans.png"),
        "./assets/icons/icon_pride_trans.png",
    ],
    [
        require.resolve("@goauthentik/brand-assets/icon_top_brand.png"),
        "./assets/icons/icon_top_brand.png",
    ],
    [
        require.resolve("@goauthentik/brand-assets/icon_top_brand.svg"),
        "./assets/icons/icon_top_brand.svg",
    ],
];

export async function copyAssets() {
    /**
     * @param {SourceDestinationPair} pair
     */
    const copy = ([from, to]) => {
        const resolvedDestination = path.resolve(DistDirectory, to);

        logger.debug(`📋 Copying assets from ${from} to ${to}`);

        return fs
            .cp(from, resolvedDestination, {
                recursive: true,
            })
            .catch((error) => {
                logger.error(`Failed to copy assets from ${from} to ${to}: ${error}`);
            });
    };

    return await Promise.all(assets.map(copy));
}
