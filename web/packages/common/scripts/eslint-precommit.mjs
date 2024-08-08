import { execFileSync } from "child_process";
import { ESLint } from "eslint";
import path from "path";
import process from "process";

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
        plugins: ["@typescript-eslint", "lit", "custom-elements", "sonarjs"],
        rules: {
            "indent": "off",
            "linebreak-style": ["error", "unix"],
            "quotes": ["error", "double", { avoidEscape: true }],
            "semi": ["error", "always"],
            "@typescript-eslint/ban-ts-comment": "off",
        },
    },
};

const eslint = new ESLint(eslintConfig);
const results = await eslint.lintFiles(["./src/**/*", "./build.mjs", "./scripts/*.mjs"]);
const formatter = await eslint.loadFormatter("stylish");
const resultText = formatter.format(results);
const errors = results.reduce((acc, result) => acc + result.errorCount, 0);

console.log(resultText);
process.exit(errors > 1 ? 1 : 0);
