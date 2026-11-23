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

export interface MdxPluginData {
    sourcePath: string | undefined;
}

type MDXOnResolveArgs = Omit<OnResolveArgs, "pluginData"> & { pluginData: MdxPluginData };

type MDXOnLoadArgs = Omit<OnLoadArgs, "pluginData"> & { pluginData?: MdxPluginData };

/**
 * Bundle markdown and MDX source into JSON modules.
 */
export function mdxPlugin({ root }: MDXPluginOptions): Plugin {
    const prefix = "~docs";
    // TODO: Replace with `resolvePackage` after NPM Workspaces support is added.
    const docsPackageRoot = path.resolve(MonoRepoRoot, "website");

    function setup(build: PluginBuild) {
        async function resolveListener(args: MDXOnResolveArgs): Promise<OnResolveResult> {
            if (!args.path.startsWith("~")) return args;

            // We explicitly convert the MDX into a JSON object for rendering, so we include the
            // `sourcePath` as a separate field from the `path`, which points to our intended
            // output.
            const sourcePath = path.join(docsPackageRoot, "docs", args.path.slice(prefix.length));

            return {
                path: sourcePath.replace(/\.mdx?$/, ".json"),
                pluginData: { sourcePath },
                pluginName,
            };
        }

        async function loadListener(args: MDXOnLoadArgs): Promise<OnLoadResult | undefined> {
            const sourcePath = args.pluginData?.sourcePath;

            if (!sourcePath) return undefined;

            const source = String(await fs.readFile(sourcePath));
            const docsPath = path.join(root, "website", "docs");
            const publicPath = path.resolve("/", path.relative(docsPath, sourcePath));
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
                // Since the resolved `.json` path is output, we have to specify the source to
                // watch.
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
