import markdown from "@jackfranklin/rollup-plugin-markdown";
import babel from "@rollup/plugin-babel";
import commonjs from "@rollup/plugin-commonjs";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import replace from "@rollup/plugin-replace";
import terser from "@rollup/plugin-terser";
import { cwd } from "process";
import copy from "rollup-plugin-copy";
import cssimport from "rollup-plugin-cssimport";
import { fileURLToPath } from "url";
import path from "path";

// https://github.com/d3/d3-interpolate/issues/58
const __dirname = fileURLToPath(new URL(".", import.meta.url));
const IGNORED_WARNINGS = /Circular dependency(.*d3-[interpolate|selection])|(.*@lit\/localize.*)/;

const ROOT = path.join(__dirname, "../../");
const DIST = path.join(ROOT, "dist");


const extensions = [".js", ".jsx", ".ts", ".tsx"];

export const resources = [
    {
        src: path.join(ROOT, "node_modules/@patternfly/patternfly/patternfly.min.css"),
        dest: DIST,
    },
    { src: "src/common/styles/*", dest: DIST },
    { src: "src/custom.css", dest: DIST },

    {
        src: path.join(ROOT, "node_modules/@patternfly/patternfly/assets/*"),
        dest: path.join(DIST, "assets/"),
    },
    { src: "src/assets/*", dest: path.join(DIST, "assets") },
    { src: "./icons/*", dest: path.join(DIST, "assets/icons") },
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

export const standalone = ["api-browser", "loading"].map((input) => {
    return {
        input: `./src/standalone/${input}`,
        output: [
            {
                format: "es",
                dir: path.join(DIST, `standalone/${input}`),
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
                dir: path.join(DIST, "flow"),
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    },
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
    // User interface
    {
        input: "./src/user/UserInterface.ts",
        output: [
            {
                format: "es",
                dir: path.join(DIST, "user"),
                sourcemap: true,
                manualChunks: manualChunks,
            },
        ],
        ...defaultOptions,
    },
];
