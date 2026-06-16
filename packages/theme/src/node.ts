/*
 * @file Node-only build helpers for `@goauthentik/theme`.
 *
 * Re-exports everything the browser entry exports, plus filesystem-touching
 * helpers that wrap styleframe's `transpile()` for use from build scripts.
 *
 * @import { OutputFile } from "@styleframe/transpiler";
 */


import type { OutputFile } from "@styleframe/transpiler";

import { writeFile } from "node:fs/promises";

import { instance } from "./shared.js";

import { transpile } from "@styleframe/transpiler";

// Re-export everything the browser entry exposes so consumers can do either
// `import { variable } from "@goauthentik/theme"` (browser-safe) or
// `import { build } from "@goauthentik/theme/build"` (Node-only) from the
// same package without juggling subpaths.
export * from "./shared.js";
export * from "./tokens/index.js";

/**
 * @typedef {object} BuildOptions
 * @property {string} [outFile] If provided, the generated CSS is written to
 *   this absolute path in addition to being returned.
 */

interface BuildOptions {
    outFile?: string;
}

/**
 * @typedef {object} BuildResult
 * @property {string} css The full CSS string emitted by styleframe.
 * @property {OutputFile[]} files Raw transpile output for callers that want
 *   to inspect every file styleframe produced.
 */

interface BuildResult {
    css: string;
    files: OutputFile[];
}

/**
 * Transpile the configured token tree to CSS.
 *
 * Equivalent to `npx styleframe build` for the css output type, but returns
 * the string directly so build scripts can post-process before writing.
 *
 * @param {BuildOptions} [options]
 * @returns {Promise<BuildResult>}
 */
export async function build(options: BuildOptions = {}): Promise<BuildResult> {
    const output = await transpile(instance, { type: "css" });
    const cssFile = output.files.find((file) => file.name.endsWith(".css"));
    const css = cssFile?.content ?? "";

    if (options.outFile) {
        await writeFile(options.outFile, css, "utf-8");
    }

    return { css, files: output.files };
}
