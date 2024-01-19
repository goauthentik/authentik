import { DIST, resources, manualChunks, isProdBuild, defaultOptions } from "../../rollup.base.mjs";
import markdown from "@jackfranklin/rollup-plugin-markdown";
import copy from "rollup-plugin-copy";
import path from "path";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import terser from "@rollup/plugin-terser";
import cssimport from "rollup-plugin-cssimport";

// Polyfills (imported first)
export const POLY = {
    input: "./src/polyfill/poly.ts",
    output: [
        {
            format: "iife",
            file: path.join(DIST, "poly.js"),
            sourcemap: true,
        },
    ],
    cache: true,
    plugins: [
        cssimport(),
        nodeResolve({ browser: true }),
        commonjs(),
        isProdBuild && terser(),
        copy({
            targets: [...resources],
            copyOnce: false,
        }),
    ].filter((p) => p),
};

export const enterprise = ["rac"].map((input) => {
    return {
        input: `./src/enterprise/${input}`,
        output: [
            {
                format: "es",
                dir: path.join(DIST, "enterprise", input),
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    };
});

export default [
    POLY,
    // Admin interface
    {
        input: "./src/admin/AdminInterface/AdminInterface.ts",
        output: [
            {
                format: "es",
                dir: path.join(DIST, "admin"),
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    },
    // Enterprise
    ...enterprise,
];
