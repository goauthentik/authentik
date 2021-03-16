import resolve from "rollup-plugin-node-resolve";
import commonjs from "rollup-plugin-commonjs";
import { terser } from "rollup-plugin-terser";
import sourcemaps from "rollup-plugin-sourcemaps";
import typescript from "@rollup/plugin-typescript";
import cssimport from "rollup-plugin-cssimport";
import copy from "rollup-plugin-copy";
import externalGlobals from "rollup-plugin-external-globals";

const resources = [
    { src: "node_modules/@patternfly/patternfly/patternfly-base.css", dest: "dist/" },
    { src: "node_modules/@patternfly/patternfly/assets/*", dest: "dist/assets/" },
    { src: "src/index.html", dest: "dist" },
    { src: "src/assets/*", dest: "dist/assets" },
    { src: "./icons/*", dest: "dist/assets/icons" },
];

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
function manualChunks(id) {
    if (id.includes("node_modules")) {
        return "vendor";
    }
    if (id.includes("src/api/")) {
        return "api";
    }
}

export default [
    {
        input: "./src/main.ts",
        output: [
            {
                format: "es",
                dir: "dist",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        plugins: [
            cssimport(),
            typescript(),
            externalGlobals({
                django: "django"
            }),
            resolve({ browser: true }),
            commonjs(),
            sourcemaps(),
            terser(),
            copy({
                targets: [...resources],
                copyOnce: false,
            }),
        ],
        watch: {
            clearScreen: false,
        },
        external: ["django"]
    },
    {
        input: "./src/flow.ts",
        output: [
            {
                format: "es",
                dir: "dist",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        plugins: [
            cssimport(),
            typescript(),
            externalGlobals({
                django: "django"
            }),
            resolve({ browser: true }),
            commonjs(),
            sourcemaps(),
            terser(),
            copy({
                targets: [...resources],
                copyOnce: false,
            }),
        ],
        watch: {
            clearScreen: false,
        },
        external: ["django"]
    },
];
