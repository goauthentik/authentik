/**
 * @import { Plugin } from "@docusaurus/types";
 */

/**
 * @returns {Plugin<void>}
 */
export default function docusaurusThemeAuthentikTOC() {
    return {
        name: "docusaurus-theme-authentik-toc",
        getThemePath() {
            return "./theme";
        },
        getTypeScriptThemePath() {
            return "./theme";
        },
    };
}
