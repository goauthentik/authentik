/**
 * @import { Plugin } from "@docusaurus/types";
 * @file Docusaurus theme plugin.
 */

/**
 * @returns {Plugin<void>}
 */
export default function docusaurusThemeAuthentik() {
    return {
        name: "docusaurus-theme-authentik",

        getThemePath() {
            return "./theme";
        },

        getTypeScriptThemePath() {
            return "./theme";
        },
    };
}
