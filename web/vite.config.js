import { createBundleDefinitions } from "#bundler/utils/node";
import { inlineCSSPlugin } from "#bundler/vite-plugin-lit-css/node";

import { defineConfig } from "vite";

export default defineConfig({
    define: createBundleDefinitions(),
    plugins: [
        // ---
        inlineCSSPlugin(),
    ],
});
