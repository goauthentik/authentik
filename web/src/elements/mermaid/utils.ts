import MermaidStyles from "./mermaid.css";

import { DOM_PURIFY_STRICT } from "#common/purify";
import { ResolvedUITheme } from "#common/theme";

import { MermaidThemeAdapter } from "#elements/mermaid/theme";

import elkLayouts from "@mermaid-js/layout-elk";
import type { Mermaid, MermaidConfig } from "mermaid";

export const DefaultMermaidConfig: Readonly<MermaidConfig> = {
    logLevel: "fatal",
    startOnLoad: false,
    htmlLabels: true,
    fontFamily: "var(--ak-font-family-sans-serif)",
    layout: "elk",
    flowchart: {
        curve: "linear",

        nodeSpacing: 25,
        rankSpacing: 25,
        wrappingWidth: 500,
    },
    theme: "base",
    securityLevel: "strict",
    dompurifyConfig: DOM_PURIFY_STRICT,
};

let lastActiveTheme: ResolvedUITheme | null = null;
let mermaid: Mermaid | null = null;

/**
 * Load the Mermaid library and initialize it with the appropriate theme based
 * on the provided UI theme.
 *
 * @remarks
 *
 * Mermaid is only loaded once and cached for subsequent calls. Note that
 * Mermaid is a singleton and does not support multiple instances with different
 * configurations. Re-initialization occurs only when the active theme changes.
 *
 * @param uiTheme The resolved UI theme to derive Mermaid colors from.
 * @returns The initialized Mermaid singleton.
 */
export async function loadMermaid(uiTheme: ResolvedUITheme): Promise<Mermaid> {
    if (!mermaid) {
        const mermaidModule = await import("mermaid");
        mermaid = mermaidModule.default;
        mermaid.registerLayoutLoaders(elkLayouts);
    }

    if (uiTheme && uiTheme === lastActiveTheme) {
        return mermaid;
    }

    await new Promise((resolve) => requestAnimationFrame(resolve));

    const computedStyle = getComputedStyle(document.documentElement);
    const darkMode = uiTheme === "dark";

    const themeAdapter = new MermaidThemeAdapter(computedStyle);
    const themeVariables = themeAdapter.toThemeVariables(darkMode);

    mermaid.initialize({
        ...DefaultMermaidConfig,
        themeVariables: {
            ...themeVariables,
        },
        darkMode,
        themeCSS: String(MermaidStyles),
    });

    lastActiveTheme = uiTheme;

    return mermaid;
}
