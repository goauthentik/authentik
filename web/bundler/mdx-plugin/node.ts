/**
 * @file Markdown plugin for ESBuild.
 *   Resolves `~docs/...` imports to the website docs tree, then compiles each
 *   `.md` / `.mdx` file to HTML at build time. The compiled HTML uses
 *   `<ak-md-a>` and `<ak-alert>` custom elements so the runtime side can
 *   stamp the HTML directly into shadow DOM without any client-side
 *   JavaScript evaluation — this is what lets the page CSP drop
 *   `'unsafe-eval'`.
 *   The on-load result is shipped via the `file` loader so the JSON travels
 *   over the existing fetch-then-set-innerHTML path used by `<ak-mdx>`. The
 *   shape is `{ content, frontmatter, publicPath, publicDirectory }` where
 *   `content` is now pre-rendered HTML rather than raw markdown source.
 *   The `file` loader takes the emitted extension from the resolved path, so
 *   imports resolve to a `.json` sibling path and carry the real source path
 *   in `pluginData`; the emitted asset is then `.json`, not `.mdx`.
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { compileMarkdown } from "./compile.ts";

import { MonoRepoRoot } from "@goauthentik/core/paths/node";

import type {
    OnLoadArgs,
    OnLoadResult,
    OnResolveArgs,
    OnResolveResult,
    Plugin,
    PluginBuild,
} from "esbuild";

const pluginName = "mdx-plugin";

export interface MDXPluginOptions {
    /**
     * Repository root.
     */
    root: string;
}

/**
 * Bundle markdown and MDX source into JSON modules.
 */
export function mdxPlugin({ root }: MDXPluginOptions): Plugin {
    const prefix = "~docs";
    // TODO: Replace with `resolvePackage` after NPM Workspaces support is added.
    const docsPackageRoot = path.resolve(MonoRepoRoot, "website");

    function setup(build: PluginBuild) {
        async function resolveListener(args: OnResolveArgs): Promise<OnResolveResult> {
            if (!args.path.startsWith("~")) return args;

            const sourcePath = path.join(docsPackageRoot, "docs", args.path.slice(prefix.length));

            return {
                path: sourcePath.replace(/\.mdx?$/, ".json"),
                pluginData: { sourcePath },
                pluginName,
            };
        }

        async function loadListener(args: OnLoadArgs): Promise<OnLoadResult | undefined> {
            const sourcePath: string | undefined = args.pluginData?.sourcePath;

            // Not one of ours: let esbuild's default JSON loader handle it.
            if (!sourcePath) return undefined;

            const source = String(await fs.readFile(sourcePath));

            const publicPath = path.resolve(
                "/",
                path.relative(path.join(root, "website", "docs"), sourcePath),
            );

            const publicDirectory = path.dirname(publicPath);

            const { html, frontmatter } = await compileMarkdown(source, publicDirectory);

            return {
                contents: JSON.stringify({
                    content: html,
                    frontmatter,
                    publicPath,
                    publicDirectory,
                }),
                loader: "file",
                // The resolved `.json` path doesn't exist; watch the real source instead.
                watchFiles: [sourcePath],
                pluginName,
            };
        }

        build.onResolve({ filter: /\.mdx?$/ }, resolveListener);
        build.onLoad({ filter: /\.json$/ }, loadListener);
    }

    return {
        name: pluginName,
        setup,
    };
}
