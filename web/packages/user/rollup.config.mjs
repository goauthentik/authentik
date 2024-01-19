import path from "path";

import { DIST, defaultOptions, manualChunks } from "../../rollup.base.mjs";

export const apiBrowser = {
    input: "./dist/index.js",
    output: [
        {
            format: "es",
            dir: path.join(DIST, "standalone", "api-browser"),
            sourcemap: true,
            manualChunks: manualChunks,
        },
    ],
    ...defaultOptions,
};

export default [apiBrowser];
