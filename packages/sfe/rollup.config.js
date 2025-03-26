import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import swc from "@rollup/plugin-swc";
import copy from "rollup-plugin-copy";

export default {
    input: "src/index.ts",
    output: {
        dir: "./dist/sfe",
        format: "cjs",
    },
    context: "window",
    plugins: [
        copy({
            targets: [
                {
                    src: "../../node_modules/bootstrap/dist/css/bootstrap.min.css",
                    dest: "./dist/sfe",
                },
            ],
        }),
        resolve({ browser: true }),
        commonjs(),
        swc({
            swc: {
                jsc: {
                    loose: false,
                    externalHelpers: false,
                    // Requires v1.2.50 or upper and requires target to be es2016 or upper.
                    keepClassNames: false,
                },
                minify: false,
                env: {
                    targets: {
                        edge: "17",
                        ie: "11",
                    },
                    mode: "entry",
                },
            },
        }),
    ],
};
