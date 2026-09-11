/**
 * @import { Plugin as VitePlugin } from "vite";
 * @file Vite plugin to inline CSS imports
 */

const CSSImportPattern = /import [\w$]+ from .+\.(css)/g;
const JavaScriptFilePattern = /\.m?(js|ts|tsx)$/;

export function inlineCSSPlugin() {
    /**
     * @satisfies {VitePlugin}
     */
    const inlineCSSPlugin = {
        name: "inline-css-plugin",
        transform: (source, id) => {
            if (!JavaScriptFilePattern.test(id)) return;

            const code = source.replace(CSSImportPattern, (match) => {
                return `${match}?inline`;
            });

            return {
                code,
            };
        },
    };

    return inlineCSSPlugin;
}
