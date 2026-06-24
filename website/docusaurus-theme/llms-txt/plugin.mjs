// docusaurus-theme/llms-txt/plugin.mjs
/* eslint-disable no-console */
/**
 * @file Docusaurus llms.txt plugin (postBuild).
 *
 * @import { LoadContext, Plugin, Props } from "@docusaurus/types"
 * @import { LLMSPluginOptions, LLMSDocInfo } from "./common.mjs"
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { LLMS_FULL_FILENAME, LLMS_TXT_FILENAME, normalizeOptions } from "./common.mjs";
import {
    applyMdExtension,
    generateFullText,
    generateIndex,
    generatePerGroupIndexes,
    renderPagePayload,
} from "./generate.mjs";
import { cleanMdxToMarkdown } from "./markdown.mjs";
import {
    assignGroup,
    collectDocFiles,
    groupLabel,
    parseDocFile,
    resolveDocumentUrl,
    resolveDocumentUrlFromSource,
} from "./node.mjs";

const PLUGIN_NAME = "ak-llms-txt-plugin";

export { assignGroup, groupLabel };

/**
 * @typedef {object} LLMSPluginContent
 * @property {string} devOutputDir
 */

/**
 * Resolve the base URL for generated links. In a Netlify deploy preview or
 * branch deploy the canonical site URL (e.g. docs.goauthentik.io) is wrong —
 * the built copy is served from `DEPLOY_PRIME_URL` — so links must point at the
 * deploy origin instead of hardcoding the production subdomain. Precedence:
 * an explicit `siteUrl` option, then the deploy-preview origin, then the
 * configured site URL.
 *
 * @param {{ siteUrl?: string }} options
 * @param {{ url: string }} siteConfig
 * @returns {string}
 */
export function resolveSiteUrl(options, siteConfig) {
    if (options.siteUrl) return options.siteUrl;
    // Netlify sets CONTEXT to one of production | deploy-preview | branch-deploy,
    // and DEPLOY_PRIME_URL to the canonical URL for the current (non-production) deploy.
    const context = process.env.CONTEXT;
    const deployURL = process.env.DEPLOY_PRIME_URL;
    if (context && context !== "production" && deployURL) return deployURL;
    return siteConfig.url;
}

/**
 * Build every output file's contents, keyed by build-relative path.
 *
 * @param {{ siteDir: string, outDir: string, siteUrl: string, title: string,
 *   description: string, routesPaths: string[], options: LLMSPluginOptions }} ctx
 * @returns {Promise<Map<string, string>>}
 */
export async function buildLLMSOutputs(ctx) {
    const options = normalizeOptions(ctx.options);

    /** @type {LLMSDocInfo[]} */
    const docs = [];
    let skippedNoRoute = 0;
    let mdxFallbacks = 0;

    for (const section of options.sections) {
        const absDir = path.resolve(ctx.siteDir, section.path);
        for (const file of collectDocFiles(absDir, options.ignoreFiles)) {
            const parsed = parseDocFile(file, absDir);
            if (!parsed) continue;

            const route = ctx.routesPaths.length
                ? resolveDocumentUrl(parsed.path, ctx.routesPaths)
                : resolveDocumentUrlFromSource(parsed, section.routeBasePath);
            if (!route) {
                // Expected for source files Docusaurus does not route (e.g.
                // historical release notes). Counted and summarized, not warned per-page.
                skippedNoRoute++;
                continue;
            }

            parsed.url = new URL(route, ctx.siteUrl).toString();
            parsed.group = assignGroup(parsed, options);
            parsed.groupLabel = groupLabel(parsed.group, options);
            parsed.content = await cleanMdxToMarkdown(parsed.content, file, () => mdxFallbacks++);
            docs.push(parsed);
        }
    }

    if (skippedNoRoute || mdxFallbacks) {
        console.log(
            `🚀 ${PLUGIN_NAME}: indexed ${docs.length} pages ` +
                `(${skippedNoRoute} skipped — no route; ${mdxFallbacks} used the regex fallback)`,
        );
    }

    /** @type {Map<string, string>} */
    const outputs = new Map();

    // Overview pages (e.g. integrations index + applications) are inlined into
    // the root index as an "## Overview" section, not listed/grouped as links.
    const overviewSet = new Set(options.overviewPages ?? []);
    const overviewDocs = docs.filter((d) => overviewSet.has(d.path));
    const tocDocs = docs.filter((d) => !overviewSet.has(d.path));

    const indexOpts = {
        title: ctx.title,
        description: ctx.description,
        crossLinks: options.crossLinks,
    };

    outputs.set(
        LLMS_TXT_FILENAME,
        generateIndex(tocDocs, { ...indexOpts, overview: overviewDocs }),
    );
    // llms-full.txt keeps the full content of every page, overview pages included.
    outputs.set(LLMS_FULL_FILENAME, generateFullText(docs, indexOpts));

    const rootUrl = new URL(`/${LLMS_TXT_FILENAME}`, ctx.siteUrl).toString();
    for (const [group, contents] of generatePerGroupIndexes(tocDocs, {
        title: ctx.title,
        description: ctx.description,
        parentUrl: rootUrl,
    })) {
        outputs.set(`${group}/${LLMS_TXT_FILENAME}`, contents);
    }

    for (const doc of docs) {
        // applyMdExtension(url) gives the absolute .md URL; derive the build path.
        const rel = applyMdExtension(doc.url).slice(ctx.siteUrl.replace(/\/+$/, "").length + 1);
        outputs.set(rel, renderPagePayload(doc));
    }

    return outputs;
}

/**
 * @param {string} outDir
 * @param {Map<string, string>} outputs
 * @returns {Promise<void>}
 */
async function writeLLMSOutputs(outDir, outputs) {
    await Promise.all(
        [...outputs.entries()].map(async ([rel, contents]) => {
            const dest = path.join(outDir, rel);
            await fs.mkdir(path.dirname(dest), { recursive: true });
            await fs.writeFile(dest, contents, "utf-8");
        }),
    );
}

/**
 * @param {LoadContext} loadContext
 * @param {LLMSPluginOptions} options
 * @returns {Plugin<LLMSPluginContent>}
 */
function akLLMSPlugin(loadContext, options) {
    const devOutputDir = path.join(loadContext.generatedFilesDir, PLUGIN_NAME);

    return {
        name: PLUGIN_NAME,

        async loadContent() {
            const outputs = await buildLLMSOutputs({
                siteDir: loadContext.siteDir,
                outDir: devOutputDir,
                siteUrl: resolveSiteUrl(options, loadContext.siteConfig),
                title: options.title ?? loadContext.siteConfig.title,
                description: options.description ?? loadContext.siteConfig.tagline ?? "",
                routesPaths: [],
                options,
            });

            await fs.rm(devOutputDir, { recursive: true, force: true });
            await writeLLMSOutputs(devOutputDir, outputs);

            return {
                devOutputDir,
            };
        },

        configureWebpack(_config, isServer, _utils, content) {
            if (isServer || !content?.devOutputDir) {
                return undefined;
            }

            /** @type {any} */
            const devServerConfig = {
                devServer: {
                    static: [
                        {
                            directory: content.devOutputDir,
                            publicPath: loadContext.baseUrl,
                        },
                    ],
                },
            };

            return devServerConfig;
        },

        /**
         * @param {Props} props
         */
        async postBuild(props) {
            console.log(`🚀 ${PLUGIN_NAME} generating llms.txt`);

            const outputs = await buildLLMSOutputs({
                siteDir: props.siteDir,
                outDir: props.outDir,
                siteUrl: resolveSiteUrl(options, props.siteConfig),
                title: options.title ?? props.siteConfig.title,
                description: options.description ?? props.siteConfig.tagline ?? "",
                routesPaths: props.routesPaths,
                options,
            });

            await writeLLMSOutputs(props.outDir, outputs);

            console.log(`✅ ${PLUGIN_NAME} wrote ${outputs.size} files`);
        },
    };
}

export default akLLMSPlugin;
