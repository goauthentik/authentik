import { execFileSync } from "child_process";
import { ESLint } from "eslint";
import fastGlob from "fast-glob";
import path from "path";
import process from "process";

const SOURCES = ["./build.mjs", "./src/**/*.ts", "./scripts/*.mjs", "./.storybook/*.ts"];

// Code assumes this script is in the './web/scripts' folder.
const projectRoot = execFileSync("git", ["rev-parse", "--show-toplevel"], {
    encoding: "utf8",
}).replace("\n", "");
process.chdir(path.join(projectRoot, "./web"));

const eslintConfig = {
    overrideConfig: {
        env: {
            browser: true,
            es2021: true,
        },
        extends: [
            "eslint:recommended",
            "plugin:@typescript-eslint/recommended",
            "plugin:lit/recommended",
            "plugin:custom-elements/recommended",
            "plugin:storybook/recommended",
        ],
        parser: "@typescript-eslint/parser",
        parserOptions: {
            ecmaVersion: 12,
            sourceType: "module",
        },
        plugins: ["@typescript-eslint", "lit", "custom-elements"],
        rules: {
            "indent": "off",
            "linebreak-style": ["error", "unix"],
            "quotes": ["error", "double", { avoidEscape: true }],
            "semi": ["error", "always"],
            "@typescript-eslint/ban-ts-comment": "off",
            "no-unused-vars": "off",
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
        },
    },
};

async function expandGlobs(globs) {
    globs = Array.isArray(globs) ? globs : [globs];
    return (
        await Promise.all(
            globs.map((g) =>
                fastGlob([g], {
                    absolute: true,
                    followSymbolicLinks: false,
                }),
            ),
        )
    ).flat();
}

const isCheckable = /\.(ts|js|mjs)$/;
const toCheck = (await expandGlobs(SOURCES)).filter((f) => isCheckable.test(f));
const eslint = new ESLint(eslintConfig);
const results = await eslint.lintFiles(toCheck);
const formatter = await eslint.loadFormatter("stylish");
const resultText = formatter.format(results);
const errors = results.reduce((acc, result) => acc + result.errorCount, 0);

console.log(resultText);
process.exit(errors > 1 ? 1 : 0);
