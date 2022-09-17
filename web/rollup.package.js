import markdown from "@jackfranklin/rollup-plugin-markdown";
import babel from "@rollup/plugin-babel";
import commonjs from "@rollup/plugin-commonjs";
import json from "@rollup/plugin-json";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import replace from "@rollup/plugin-replace";
import typescript from "@rollup/plugin-typescript";
import copy from "rollup-plugin-copy";
import cssimport from "rollup-plugin-cssimport";
import { terser } from "rollup-plugin-terser";

import { apiBasePath, extensions, isProdBuild, resources } from "./rollup.config.js";

export default {
    input: "./src/package/index.ts",
    output: [
        {
            format: "es",
            dir: "dist/package",
            sourcemap: true,
        },
    ],
    plugins: [
        cssimport(),
        markdown(),
        json(),
        nodeResolve({ extensions, browser: true }),
        commonjs(),
        replace({
            "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
            "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
            "preventAssignment": true,
        }),
        typescript({
            compilerOptions: {
                rootDir: "src",
                strict: true,
                paths: {
                    "@goauthentik/web/*": ["src/*"],
                    "@goauthentik/docs/*": ["../website/docs/*"],
                },
                baseUrl: ".",
                esModuleInterop: true,
                skipLibCheck: true,
                forceConsistentCasingInFileNames: true,
                experimentalDecorators: true,
                resolveJsonModule: true,
                sourceMap: true,
                target: "esnext",
                module: "esnext",
                moduleResolution: "node",
                lib: [
                    "ES5",
                    "ES2015",
                    "ES2016",
                    "ES2017",
                    "ES2018",
                    "ES2019",
                    "ES2020",
                    "ESNext",
                    "DOM",
                    "DOM.Iterable",
                    "WebWorker",
                ],
                plugins: [
                    {
                        name: "ts-lit-plugin",
                        strict: true,
                        rules: {
                            "no-unknown-tag-name": "off",
                        },
                    },
                ],
                declaration: true,
                emitDeclarationOnly: true,
                outDir: "dist/package",
                declarationMap: true,
            },
        }),
        copy({
            targets: [...resources],
            copyOnce: false,
        }),
        isProdBuild && terser(),
    ].filter((p) => p),
    watch: {
        clearScreen: false,
    },
    preserveEntrySignatures: "strict",
    cache: true,
    context: "window",
};
