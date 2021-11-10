import babel from "@rollup/plugin-babel";
import commonjs from "@rollup/plugin-commonjs";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import replace from "@rollup/plugin-replace";
import copy from "rollup-plugin-copy";
import cssimport from "rollup-plugin-cssimport";
import sourcemaps from "rollup-plugin-sourcemaps";
import { terser } from "rollup-plugin-terser";

const extensions = [".js", ".jsx", ".ts", ".tsx"];

const resources = [
    { src: "node_modules/rapidoc/dist/rapidoc-min.js", dest: "dist/" },

    {
        src: "node_modules/@patternfly/patternfly/patternfly.min.css",
        dest: "dist/",
    },
    {
        src: "node_modules/@patternfly/patternfly/patternfly-base.css",
        dest: "dist/",
    },
    {
        src: "node_modules/@patternfly/patternfly/components/Page/page.css",
        dest: "dist/",
    },
    {
        src: "node_modules/@patternfly/patternfly/components/EmptyState/empty-state.css",
        dest: "dist/",
    },
    {
        src: "node_modules/@patternfly/patternfly/components/Spinner/spinner.css",
        dest: "dist/",
    },
    { src: "src/authentik.css", dest: "dist/" },

    {
        src: "node_modules/@patternfly/patternfly/assets/*",
        dest: "dist/assets/",
    },
    { src: "src/assets/*", dest: "dist/assets" },
    { src: "./icons/*", dest: "dist/assets/icons" },
];

// eslint-disable-next-line no-undef
const isProdBuild = process.env.NODE_ENV === "production";
// eslint-disable-next-line no-undef
const apiBasePath = process.env.AK_API_BASE_PATH || "";

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
function manualChunks(id) {
    if (id.includes("@goauthentik/api")) {
        return "api";
    }
    if (id.includes("locales")) {
        const parts = id.split("/");
        const file = parts[parts.length - 1];
        return "locale-" + file.replace(".ts", "");
    }
    if (id.includes("node_modules")) {
        if (id.includes("codemirror")) {
            return "vendor-cm";
        }
        return "vendor";
    }
}

const PLUGINS = [
    cssimport(),
    nodeResolve({ extensions, browser: true }),
    commonjs(),
    babel({
        extensions,
        babelHelpers: "runtime",
        include: ["src/**/*"],
    }),
    replace({
        "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
        "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
        "preventAssignment": true,
    }),
    sourcemaps(),
    isProdBuild && terser(),
].filter((p) => p);

export default [
    // Polyfills (imported first)
    {
        input: "./poly.ts",
        output: [
            {
                format: "iife",
                file: "dist/poly.js",
                sourcemap: true,
            },
        ],
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
        watch: {
            clearScreen: false,
        },
    },
    // Flow interface
    {
        input: "./src/interfaces/FlowInterface.ts",
        context: "window",
        output: [
            {
                format: "es",
                dir: "dist/flow",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        plugins: PLUGINS,
        watch: {
            clearScreen: false,
        },
    },
    // Admin interface
    {
        input: "./src/interfaces/AdminInterface.ts",
        context: "window",
        output: [
            {
                format: "es",
                dir: "dist/admin",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        plugins: PLUGINS,
        watch: {
            clearScreen: false,
        },
    },
    // User interface
    {
        input: "./src/interfaces/UserInterface.ts",
        context: "window",
        output: [
            {
                format: "es",
                dir: "dist/user",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        plugins: PLUGINS,
        watch: {
            clearScreen: false,
        },
    },
];
