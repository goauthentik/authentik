import "@goauthentik/core/environment/load/node";

import { existsSync } from "node:fs";
import * as fs from "node:fs/promises";
import { createRequire } from "node:module";
import * as path from "node:path";

import { ConsoleLogger } from "#logger/node";
import { DistDirectory, EntryPoint, PackageRoot } from "#paths/node";

import { MonoRepoRoot } from "@goauthentik/core/paths/node";

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

// Bundled hexworld basemap. The archive is committed at
// packages/geo/tiles/hexworld.pmtiles (see the geo package README); glyphs
// are gitignored and fetched from the Protomaps CDN on first build, then
// cached in tiles/fonts/ so subsequent builds reuse them.
const HEXWORLD_SRC = path.resolve(MonoRepoRoot, "packages", "geo", "tiles");
const HEXWORLD_DEST = path.resolve(DistDirectory, "assets", "maps");
const GLYPH_BASE =
    process.env.AUTHENTIK_HEXWORLD_GLYPHS ??
    "https://raw.githubusercontent.com/protomaps/basemaps-assets/main/fonts";
const GLYPH_FONTS = ["Noto Sans Regular", "Noto Sans Medium"];
const GLYPH_RANGES = ["0-255", "256-511"];

/**
 * @param {string} fontsDir
 */
async function ensureGlyphs(fontsDir) {
    for (const font of GLYPH_FONTS) {
        const dir = path.resolve(fontsDir, font);
        await fs.mkdir(dir, { recursive: true });
        for (const range of GLYPH_RANGES) {
            const dest = path.resolve(dir, `${range}.pbf`);
            if (existsSync(dest)) continue;
            const url = `${GLYPH_BASE}/${encodeURIComponent(font)}/${range}.pbf`;
            const res = await fetch(url);
            if (!res.ok) throw new Error(`glyph fetch failed: ${url} → HTTP ${res.status}`);
            await fs.writeFile(dest, Buffer.from(await res.arrayBuffer()));
            logger.info(`fetched glyph ${font}/${range}.pbf`);
        }
    }
}

async function copyHexworld() {
    const archive = path.resolve(HEXWORLD_SRC, "hexworld.pmtiles");
    if (!existsSync(archive)) {
        throw new Error(
            `hexworld.pmtiles missing at ${archive}. The archive is committed to git; ` +
                "if it disappeared, restore from HEAD or regenerate via " +
                "`pnpm --dir packages/geo run hexworld:build`.",
        );
    }
    const fonts = path.resolve(HEXWORLD_SRC, "fonts");
    await ensureGlyphs(fonts);
    await fs.mkdir(HEXWORLD_DEST, { recursive: true });
    await fs.cp(archive, path.resolve(HEXWORLD_DEST, "hexworld.pmtiles"));
    await fs.cp(fonts, path.resolve(HEXWORLD_DEST, "fonts"), { recursive: true });
    logger.debug("📋 Bundled hexworld basemap");
}

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

    return await Promise.all([...assets.map(copy), copyHexworld()]);
}
