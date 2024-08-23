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
    fix: true,
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
            "plugin:sonarjs/recommended",
        ],
        parser: "@typescript-eslint/parser",
        parserOptions: {
            ecmaVersion: 12,
            sourceType: "module",
            project: true,
        },
        plugins: ["@typescript-eslint", "lit", "custom-elements", "sonarjs"],
        ignorePatterns: ["authentik-live-tests/**", "./.storybook/**/*.ts"],
        rules: {
            "indent": "off",
            "linebreak-style": ["error", "unix"],
            "quotes": ["error", "double", { avoidEscape: true }],
            "semi": ["error", "always"],
            "@typescript-eslint/ban-ts-comment": "off",
            "no-unused-vars": "off",
            "sonarjs/cognitive-complexity": ["warn", 9],
            "sonarjs/no-duplicate-string": "off",
            "sonarjs/no-nested-template-literals": "off",
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
            "no-console": ["error", { allow: ["debug", "warn", "error"] }],
        },
    },
};

const updated = ["./src/", "./build.mjs", "./scripts/*.mjs"];

const eslint = new ESLint(eslintConfig);
const results = await eslint.lintFiles(updated);
const formatter = await eslint.loadFormatter("stylish");
const resultText = formatter.format(results);
const errors = results.reduce((acc, result) => acc + result.errorCount, 0);

console.log(resultText);
process.exit(errors > 1 ? 1 : 0);
