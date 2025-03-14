/**
 * @import {Options as HighlightOptions} from 'rehype-highlight'
 * @import {CompileOptions} from '@mdx-js/mdx'
 * @import {mdxmermaid} from 'mdx-mermaid'
 * @import {Message,
      OnLoadArgs,
      OnLoadResult,
      Plugin,
      PluginBuild
 * } from 'esbuild'
 */
import { run as runMDX } from "@mdx-js/mdx";
import { createFormatAwareProcessors } from "@mdx-js/mdx/internal-create-format-aware-processors";
import { extnamesToRegex } from "@mdx-js/mdx/internal-extnames-to-regex";
import apacheGrammar from "highlight.js/lib/languages/apache";
import diffGrammar from "highlight.js/lib/languages/diff";
import confGrammar from "highlight.js/lib/languages/ini";
import nginxGrammar from "highlight.js/lib/languages/nginx";
import { common } from "lowlight";
import mdxMermaid from "mdx-mermaid";
import { Mermaid } from "mdx-mermaid/lib/Mermaid";
import assert from "node:assert";
import fs from "node:fs/promises";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import * as runtime from "react/jsx-runtime";
import rehypeHighlight from "rehype-highlight";
import remarkDirective from "remark-directive";
import remarkFrontmatter from "remark-frontmatter";
import remarkGFM from "remark-gfm";
import remarkMdxFrontmatter from "remark-mdx-frontmatter";
import remarkParse from "remark-parse";
import { SourceMapGenerator } from "source-map";
import { VFile } from "vfile";
import { VFileMessage } from "vfile-message";

import { remarkAdmonition } from "./remark/remark-admonition.mjs";
import { remarkHeadings } from "./remark/remark-headings.mjs";
import { remarkLinks } from "./remark/remark-links.mjs";
import { remarkLists } from "./remark/remark-lists.mjs";

/**
 * @typedef {Omit<OnLoadArgs, 'pluginData'> & LoadDataFields} LoadData
 *   Data passed to `onload`.
 *
 * @typedef LoadDataFields
 *   Extra fields given in `data` to `onload`.
 * @property {PluginData | null | undefined} [pluginData]
 *   Plugin data.
 *
 * @typedef {CompileOptions} Options
 *   Configuration.
 *
 *   Options are the same as `compile` from `@mdx-js/mdx`.
 *
 * @typedef PluginData
 *   Extra data passed.
 * @property {Buffer | string | null | undefined} [contents]
 *   File contents.
 *
 * @typedef State
 *   Info passed around.
 * @property {string} doc
 *   File value.
 * @property {string} name
 *   Plugin name.
 * @property {string} path
 *   File path.
 */

const eol = /\r\n|\r|\n|\u2028|\u2029/g;

const name = "@mdx-js/esbuild";

/**
 * Compile MDX to HTML.
 * *
 * @param {Readonly<Options> | null | undefined} [mdxOptions]
 *   Configuration (optional).
 * @return {Plugin}
 *   Plugin.
 */
export function mdxPlugin(mdxOptions) {
    /** @type {mdxmermaid.Config} */
    const mermaidConfig = {
        output: "svg",
    };

    /**
     * @type {HighlightOptions}
     */
    const highlightThemeOptions = {
        languages: {
            ...common,
            nginx: nginxGrammar,
            apache: apacheGrammar,
            conf: confGrammar,
            diff: diffGrammar,
        },
    };

    const { extnames, process } = createFormatAwareProcessors({
        ...mdxOptions,
        SourceMapGenerator,
        outputFormat: "function-body",

        remarkPlugins: [
            remarkParse,
            remarkDirective,
            remarkAdmonition,
            remarkGFM,
            remarkFrontmatter,
            remarkMdxFrontmatter,
            remarkHeadings,
            remarkLinks,
            remarkLists,
            [mdxMermaid, mermaidConfig],
        ],
        rehypePlugins: [[rehypeHighlight, highlightThemeOptions]],
    });

    return { name, setup };

    /**
     * @param {PluginBuild} build
     *   Build.
     * @returns {undefined}
     *   Nothing.
     */
    function setup(build) {
        build.onLoad({ filter: extnamesToRegex(extnames) }, onload);

        /**
         * @param {LoadData} data
         *   Data.
         * @returns {Promise<OnLoadResult>}
         *   Result.
         */
        async function onload(data) {
            const document = String(
                data.pluginData &&
                    data.pluginData.contents !== null &&
                    data.pluginData.contents !== undefined
                    ? data.pluginData.contents
                    : await fs.readFile(data.path),
            );

            /** @type {State} */
            const state = {
                doc: document,
                name,
                path: data.path,
            };

            let file = new VFile({
                path: data.path,
                value: document,
            });

            /** @type {string | undefined} */
            let value;

            /** @type {Array<VFileMessage>} */
            let messages = [];

            /** @type {Array<Message>} */
            const errors = [];

            /** @type {Array<Message>} */
            const warnings = [];

            /**
             * @type {React.ComponentType<{children: React.ReactNode, frontmatter: Record<string, string>}>}
             */
            const wrapper = ({ children, frontmatter }) => {
                const title = frontmatter.title;
                const nextChildren = React.Children.toArray(children);

                if (title) {
                    nextChildren.unshift(React.createElement("h1", { key: "title" }, title));
                }

                return React.createElement(React.Fragment, null, nextChildren);
            };

            try {
                file = await process(file);
                const { default: Content, ...mdxExports } = await runMDX(file, {
                    ...runtime,
                    useMDXComponents: () => {
                        return {
                            mermaid: Mermaid,
                            Mermaid,
                        };
                    },
                    baseUrl: import.meta.url,
                });

                const { frontmatter = {} } = mdxExports;
                const result = renderToStaticMarkup(
                    Content({
                        frontmatter,
                        components: {
                            wrapper,
                        },
                    }),
                );

                value = result;

                messages = file.messages;
            } catch (error_) {
                const cause = /** @type {VFileMessage | Error} */ (error_);

                console.error(cause);

                const message =
                    "reason" in cause
                        ? cause
                        : new VFileMessage("Cannot process MDX file with esbuild", {
                              cause,
                              ruleId: "process-error",
                              source: "@mdx-js/esbuild",
                          });

                message.fatal = true;
                messages.push(message);
            }

            for (const message of messages) {
                const list = message.fatal ? errors : warnings;
                list.push(vfileMessageToEsbuild(state, message));
            }

            // Safety check: the file has a path, so there has to be a `dirname`.
            assert(file.dirname, "expected `dirname` to be defined");

            return {
                contents: value || "",
                loader: "text",
                errors,
                resolveDir: path.resolve(file.cwd, file.dirname),
                warnings,
            };
        }
    }
}

/**
 * @param {Readonly<State>} state
 *   Info passed around.
 * @param {Readonly<VFileMessage>} message
 *   VFile message or error.
 * @returns {Message}
 *   ESBuild message.
 */
function vfileMessageToEsbuild(state, message) {
    const place = message.place;
    const start = place ? ("start" in place ? place.start : place) : undefined;
    const end = place && "end" in place ? place.end : undefined;
    let length = 0;
    let lineStart = 0;
    let line = 0;
    let column = 0;

    if (start && start.offset !== undefined) {
        line = start.line;
        column = start.column - 1;
        lineStart = start.offset - column;
        length = 1;

        if (end && end.offset !== undefined) {
            length = end.offset - start.offset;
        }
    }

    eol.lastIndex = lineStart;

    const match = eol.exec(state.doc);
    const lineEnd = match ? match.index : state.doc.length;

    return {
        detail: message,
        id: "",
        location: {
            column,
            file: state.path,
            length: Math.min(length, lineEnd),
            line,
            lineText: state.doc.slice(lineStart, lineEnd),
            namespace: "file",
            suggestion: "",
        },
        notes: [],
        pluginName: state.name,
        text: message.reason,
    };
}
