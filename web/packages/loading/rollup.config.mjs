import path from "path";

import { DIST, defaultOptions, manualChunks } from "../../rollup.base.mjs";

export const loading = {
    input: "./dist/index.js",
    output: [
        {
            format: "es",
            dir: path.join(DIST, "standalone", "loading"),
            sourcemap: true,
            manualChunks: manualChunks,
        },
    ],
    ...defaultOptions,
};

export default [loading];
