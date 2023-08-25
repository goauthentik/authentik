import markdown from "@jackfranklin/rollup-plugin-markdown";
import babel from "@rollup/plugin-babel";
import commonjs from "@rollup/plugin-commonjs";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import replace from "@rollup/plugin-replace";
import terser from "@rollup/plugin-terser";
import { cwd } from "process";
import copy from "rollup-plugin-copy";
import cssimport from "rollup-plugin-cssimport";

// https://github.com/d3/d3-interpolate/issues/58
const IGNORED_WARNINGS = /Circular dependency(.*d3-[interpolate|selection])|(.*@lit\/localize.*)/;

const extensions = [".js", ".jsx", ".ts", ".tsx"];

export const resources = [
    {
        src: "node_modules/@patternfly/patternfly/patternfly.min.css",
        dest: "dist/",
    },
    { src: "src/common/styles/*", dest: "dist/" },
    { src: "src/custom.css", dest: "dist/" },

    {
        src: "node_modules/@patternfly/patternfly/assets/*",
        dest: "dist/assets/",
    },
    { src: "src/assets/*", dest: "dist/assets" },
    { src: "./icons/*", dest: "dist/assets/icons" },
];

// eslint-disable-next-line no-undef
export const isProdBuild = process.env.NODE_ENV === "production";
// eslint-disable-next-line no-undef
export const apiBasePath = process.env.AK_API_BASE_PATH || "";

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function manualChunks(id) {
    if (id.endsWith(".md")) {
        return "docs";
    }
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

export const defaultOptions = {
    plugins: [
        cssimport(),
        markdown(),
        nodeResolve({ extensions, browser: true }),
        commonjs(),
        babel({
            extensions,
            babelHelpers: "runtime",
            include: ["src/**/*"],
        }),
        replace({
            "process.env.NODE_ENV": JSON.stringify(isProdBuild ? "production" : "development"),
            "process.env.CWD": JSON.stringify(cwd()),
            "process.env.AK_API_BASE_PATH": JSON.stringify(apiBasePath),
            "preventAssignment": true,
        }),
        isProdBuild && terser(),
    ].filter((p) => p),
    watch: {
        clearScreen: false,
    },
    preserveEntrySignatures: "strict",
    cache: true,
    context: "window",
    onwarn: function (warning, warn) {
        if (IGNORED_WARNINGS.test(warning)) {
            return;
        }
        if (warning.code === "UNRESOLVED_IMPORT") {
            throw Object.assign(new Error(), warning);
        }
        warn(warning);
    },
};

// Polyfills (imported first)
export const POLY = {
    input: "./src/polyfill/poly.ts",
    output: [
        {
            format: "iife",
            file: "dist/poly.js",
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

export const standalone = ["api-browser", "loading"].map((input) => {
    return {
        input: `./src/standalone/${input}`,
        output: [
            {
                format: "es",
                dir: `dist/standalone/${input}`,
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    };
});

export default [
    POLY,
    // Standalone
    ...standalone,
    // Flow interface
    {
        input: "./src/flow/FlowInterface.ts",
        output: [
            {
                format: "es",
                dir: "dist/flow",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    },
    // Admin interface
    {
        input: "./src/admin/AdminInterface.ts",
        output: [
            {
                format: "es",
                dir: "dist/admin",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    },
    // User interface
    {
        input: "./src/user/UserInterface.ts",
        output: [
            {
                format: "es",
                dir: "dist/user",
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    },
];
