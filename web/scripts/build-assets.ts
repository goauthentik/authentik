import "@goauthentik/core/environment/load/node";
import { existsSync } from "node:fs";
import { mkdir, cp } from "node:fs/promises";
import { createRequire } from "node:module";
import { join, dirname, resolve } from "node:path";

import { ConsoleLogger } from "#logger/node";
import { DistDirectory, EntryPoint, PackageRoot } from "#paths/node";

import { MonoRepoRoot } from "@goauthentik/core/paths/node";

const require = createRequire(import.meta.url);
const logger = ConsoleLogger.child({ name: "Assets" });

type SourceDestinationPair = [from: string, to: string];

const assets: SourceDestinationPair[] = [
    [
        join(dirname(EntryPoint.StandaloneLoading.in), "startup"),
        dirname(EntryPoint.StandaloneLoading.out),
    ],
    [resolve(PackageRoot, "src", "assets", "images"), "./assets/images"],
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
    [
        require.resolve("maplibre-gl/dist/maplibre-gl-worker.mjs"),
        "./assets/maps/maplibre-gl-worker.mjs",
    ],
];

// Bundled hexworld basemap. Both the archive and the Latin Noto Sans glyph
// ranges (SIL OFL, see packages/geo/tiles/fonts/OFL.txt) are committed to git,
// so the copy is a pure filesystem step — the build never reaches the
// network for basemap assets.
const HEXWORLD_SRC = resolve(MonoRepoRoot, "packages", "geo", "tiles");
const HEXWORLD_DEST = resolve(DistDirectory, "assets", "maps");

async function copyHexworld() {
    const archive = resolve(HEXWORLD_SRC, "hexworld.pmtiles");

    if (!existsSync(archive)) {
        throw new Error(
            `hexworld.pmtiles missing at ${archive}. The archive is committed to git; ` +
                "if it disappeared, restore from HEAD or regenerate via " +
                "`pnpm --dir packages/geo run hexworld:build`.",
        );
    }

    const fonts = resolve(HEXWORLD_SRC, "fonts");

    if (!existsSync(fonts)) {
        throw new Error(
            `hexworld fonts missing at ${fonts}. The glyph ranges are committed to git; ` +
                "restore from HEAD.",
        );
    }

    await mkdir(HEXWORLD_DEST, { recursive: true });
    await cp(archive, resolve(HEXWORLD_DEST, "hexworld.pmtiles"));
    await cp(fonts, resolve(HEXWORLD_DEST, "fonts"), { recursive: true });

    logger.debug("📋 Bundled hexworld basemap");
}

export async function copyAssets() {
    const copy = ([from, to]: SourceDestinationPair) => {
        const resolvedDestination = resolve(DistDirectory, to);

        logger.debug(`📋 Copying assets from ${from} to ${to}`);

        return cp(from, resolvedDestination, {
            recursive: true,
        }).catch((error) => {
            logger.error(`Failed to copy assets from ${from} to ${to}: ${error}`);
        });
    };

    return await Promise.all([...assets.map(copy), copyHexworld()]);
}
