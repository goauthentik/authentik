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
            "plugin:sonarjs/recommended",
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
            "sonarjs/cognitive-complexity": ["error", 9],
            "sonarjs/no-duplicate-string": "off",
            "sonarjs/no-nested-template-literals": "off",
        },
    },
};

const porcelainV1 = /^(..)\s+(.*$)/;
const gitStatus = execFileSync("git", ["status", "--porcelain", "."], { encoding: "utf8" });

const statuses = gitStatus.split("\n").reduce((acc, line) => {
    const match = porcelainV1.exec(line.replace("\n"));
    if (!match) {
        return acc;
    }
    const [status, path] = Array.from(match).slice(1, 3);
    return [...acc, [status, path.split("\x00")[0]]];
}, []);

const isModified = /^(M|\?|\s)(M|\?|\s)/;
const modified = (s) => isModified.test(s);

const isCheckable = /\.(ts|js|mjs)$/;
const checkable = (s) => isCheckable.test(s);

const updated = statuses.reduce(
    (acc, [status, filename]) =>
        modified(status) && checkable(filename) ? [...acc, path.join(projectRoot, filename)] : acc,
    [],
);

const eslint = new ESLint(eslintConfig);
const results = await eslint.lintFiles(updated);
const formatter = await eslint.loadFormatter("stylish");
const resultText = formatter.format(results);
const errors = results.reduce((acc, result) => acc + result.errorCount, 0);

console.log(resultText);
process.exit(errors > 1 ? 1 : 0);
