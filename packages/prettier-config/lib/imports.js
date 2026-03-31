/**
 * @file Prettier import plugin.
 *
 * @import { Plugin, ParserOptions } from "prettier";
 */

import { createRequire } from "node:module";

import { formatSourceFromFile } from "format-imports";
import { parsers as babelParsers } from "prettier/plugins/babel";
import { parsers as typescriptParsers } from "prettier/plugins/typescript";

const require = createRequire(`${process.cwd()}/`);
const AK_KEEP_UNUSED_IMPORTS = !!process.env.AK_KEEP_UNUSED_IMPORTS;

/**
 * @param {string} name
 * @returns {string | null}
 */
function resolveModule(name) {
    try {
        return require.resolve(name);
    } catch (_error) {
        return null;
    }
}

const webSubmodules = [
    // ---
    "common",
    "elements",
    "components",
    "user",
    "admin",
    "flow",
];

/**
 * Ensure that every import without an extension adds one.
 * @param {string} input
 * @returns {string}
 */
function normalizeExtensions(input) {
    return input.replace(/(?:import|from)\s*["']((?:\.\.?\/).*?)(?<!\.\w+)["']/gm, (line, path) => {
        return line.replace(path, `${path}.js`);
    });
}

/**
 * @param {string} filepath
 * @param {string} input
 * @returns {string}
 */
function normalizeImports(filepath, input) {
    let output = input;

    // Replace all TypeScript imports with the paths resolved by Node/Browser import maps.

    for (const submodule of webSubmodules) {
        const legacyPattern = new RegExp(
            [
                // ---
                `(?:import|from)`,
                `\\(?\\n?\\s*`,
                `"(?<suffix>@goauthentik/${submodule}/)`,

                `(?<path>[^"'.]+)`,
                `(?:.[^"']+)?["']`,
                `\\n?\\s*\\)?;`,
            ].join(""),
            "gm",
        );

        output = output.replace(
            legacyPattern,
            /**
             * @param {string} line
             * @param {string} suffix
             * @param {string} path
             */
            (line, suffix, path) => {
                const exported = `@goauthentik/web/${submodule}/${path}`;
                let imported = `#${submodule}/${path}`;

                let module = resolveModule(`${exported}.ts`);

                if (!module) {
                    module = resolveModule(`${exported}/index.ts`);
                    imported += "/index";
                }

                if (imported.endsWith(".css")) {
                    imported += ".js";
                }

                if (!module) {
                    console.warn(`\nCannot resolve module ${exported} from ${filepath}`, {
                        line,
                        path,
                        exported,
                        imported,
                        module,
                    });

                    process.exit(1);
                }

                return (
                    line
                        // ---
                        .replace(suffix + path, imported)
                        .replace(`${imported}.js`, imported)
                );
            },
        );
    }

    return output;
}

const useLegacyCleanup = process.env.AK_FIX_LEGACY_IMPORTS === "true";

/**
 * @param {string} input
 * @param {ParserOptions} options
 */
const preprocess = (input, { filepath, printWidth }) => {
    if (input?.includes("ts-import-sorter: disable")) {
        return input;
    }

    let output = input;

    if (output.startsWith("/**\n")) {
        output = output.replace(/(^\s\*\/\n)(import)/m, "$1\n$2");
    }

    if (useLegacyCleanup) {
        output = normalizeExtensions(input);
        output = normalizeImports(filepath, output);
    }

    const value = formatSourceFromFile.sync(output, filepath, {
        nodeProtocol: "always",
        maxLineLength: printWidth,
        wrappingStyle: "prettier",
        keepUnused: AK_KEEP_UNUSED_IMPORTS ? [".*"] : [],
        groupRules: [
            "^node:",
            "^[./]",
            ...webSubmodules.map((submodule) => `^(@goauthentik/|#)${submodule}.+`),

            "^#.+",
            "^@goauthentik.+",

            {}, // Other imports.

            "^(@?)lit(.*)$",
            "\\.css$",
            "^@goauthentik/api$",
        ],
    });

    return value || input;
};

/**
 * @type {Plugin}
 */
const importsPlugin = {
    parsers: {
        typescript: {
            ...typescriptParsers.typescript,
            preprocess,
        },
        babel: {
            ...babelParsers.babel,
            preprocess,
        },
    },
};

export default importsPlugin;
