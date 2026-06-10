import { DOM_PURIFY_STRICT } from "#common/purify";
import { ResolvedUITheme } from "#common/theme";

import type { Mermaid, MermaidConfig } from "mermaid";

export const DefaultMermaidConfig: Readonly<MermaidConfig> = {
    logLevel: "fatal",
    startOnLoad: false,
    flowchart: {
        curve: "linear",
    },
    htmlLabels: false,
    securityLevel: "strict",
    dompurifyConfig: DOM_PURIFY_STRICT,
};

let lastActiveTheme: ResolvedUITheme | null = null;
let mermaid: Mermaid | null = null;

/**
 * Load the Mermaid library and initialize it with the appropriate theme based on the provided UI theme.
 *
 * @remarks
 *
 * Mermaid is only loaded once and cached for subsequent calls. Note that
 * Mermaid is a singleton and does not support multiple instances with different configurations.
 */
export async function loadMermaid(uiTheme: ResolvedUITheme): Promise<Mermaid> {
    if (!mermaid) {
        const mermaidModule = await import("mermaid");
        mermaid = mermaidModule.default;
    }

    if (uiTheme && uiTheme === lastActiveTheme) {
        return mermaid;
    }

    const theme = uiTheme === "dark" ? "dark" : "default";

    mermaid.initialize({
        ...DefaultMermaidConfig,
        theme,
        darkMode: uiTheme === "dark",
    });

    lastActiveTheme = uiTheme;

    return mermaid;
}
