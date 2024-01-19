import markdown from "@jackfranklin/rollup-plugin-markdown";
import babel from "@rollup/plugin-babel";
import commonjs from "@rollup/plugin-commonjs";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import replace from "@rollup/plugin-replace";
import terser from "@rollup/plugin-terser";
import path from "path";
import { cwd } from "process";
import cssimport from "rollup-plugin-cssimport";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
export const ROOT = path.join(__dirname, ".");
export const DIST = path.join(ROOT, "dist");

// https://github.com/d3/d3-interpolate/issues/58
const IGNORED_WARNINGS = /Circular dependency(.*d3-[interpolate|selection])|(.*@lit\/localize.*)/;

const extensions = [".js", ".ts"];

// eslint-disable-next-line no-undef
export const isProdBuild = process.env.NODE_ENV === "production";

// eslint-disable-next-line no-undef
export const apiBasePath = process.env.AK_API_BASE_PATH || "";

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
