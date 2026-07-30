/**
 * @file Docusaurus theme plugin.
 * @import { Plugin } from "@docusaurus/types";
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
