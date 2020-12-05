import resolve from "rollup-plugin-node-resolve";
import commonjs from "rollup-plugin-commonjs";
import minifyHTML from "rollup-plugin-minify-html-literals";
import { terser } from "rollup-plugin-terser";
import sourcemaps from "rollup-plugin-sourcemaps";
import typescript from "@rollup/plugin-typescript";
import cssimport from "rollup-plugin-cssimport";
import copy from "rollup-plugin-copy";
import externalGlobals from "rollup-plugin-external-globals";

const resources = [
    { src: "node_modules/@patternfly/patternfly/patternfly.css", dest: "dist/" },
    { src: "node_modules/@patternfly/patternfly/patternfly-addons.css", dest: "dist/" },
    { src: "node_modules/@fortawesome/fontawesome-free/css/fontawesome.min.css", dest: "dist/" },
    { src: "node_modules/@patternfly/patternfly/assets/*", dest: "dist/assets/" },
    { src: "src/index.html", dest: "dist" },
    { src: "src/authentik.css", dest: "dist" },
    { src: "src/assets/*", dest: "dist/assets" },
    { src: "../icons/*", dest: "dist/assets/icons" },
];

export default [
    {
        input: "./src/main.ts",
        output: [
            {
                format: "es",
                dir: "dist",
                sourcemap: true,
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
            minifyHTML(),
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
