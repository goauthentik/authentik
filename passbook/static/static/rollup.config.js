import resolve from "rollup-plugin-node-resolve";
import commonjs from "rollup-plugin-commonjs";
import minifyHTML from "rollup-plugin-minify-html-literals";
import { terser } from "rollup-plugin-terser";
import sourcemaps from "rollup-plugin-sourcemaps";
import typescript from "@rollup/plugin-typescript";
import cssimport from "rollup-plugin-cssimport";
import copy from "rollup-plugin-copy";

const resources = [{ src: "src/index.html", dest: "dist" }];

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
    },
];
