import { globalAK } from "@goauthentik/common/global";
import {
    StyleSheetInit,
    StyleSheetParent,
    appendStyleSheet,
    createStyleSheetUnsafe,
    removeStyleSheet,
    resolveStyleSheetParent,
} from "@goauthentik/common/stylesheets";
import { ResolvedUITheme, createUIThemeEffect, resolveUITheme } from "@goauthentik/common/theme";
import { type ThemedElement } from "@goauthentik/common/theme";

import { localized } from "@lit/localize";
import { CSSResultGroup, CSSResultOrNative, LitElement } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import OneDark from "@goauthentik/common/styles/one-dark.css";
import ThemeDark from "@goauthentik/common/styles/theme-dark.css";

import { CurrentBrand, UiThemeEnum } from "@goauthentik/api";

// Re-export the theme helpers
export { rootInterface } from "@goauthentik/common/theme";

export interface AKElementInit {
    brand?: Partial<CurrentBrand>;
    styleParents?: StyleSheetParent[];
}

@localized()
export class AKElement extends LitElement implements ThemedElement {
    /**
     * The resolved theme of the current element.
     *
     * @remarks
     *
     * Unlike the browser's current color scheme, this is a value that can be
     * resolved to a specific theme, i.e. dark or light.
     */
    @property({
        attribute: "theme",
        type: String,
        reflect: true,
    })
    public activeTheme: ResolvedUITheme;

    protected static finalizeStyles(styles?: CSSResultGroup): CSSResultOrNative[] {
        // Ensure all style sheets being passed are really style sheets.
        const baseStyles: StyleSheetInit[] = [AKGlobal, OneDark];

        if (!styles) return baseStyles.map(createStyleSheetUnsafe);

        if (Array.isArray(styles)) {
            return [
                //---
                ...(styles as unknown as CSSResultOrNative[]),
                ...baseStyles,
            ].flatMap(createStyleSheetUnsafe);
        }
        return [styles, ...baseStyles].map(createStyleSheetUnsafe);
    }

    constructor(init?: AKElementInit) {
        super();

        const config = globalAK();
        const { brand = config.brand, styleParents = [] } = init || {};

        this.activeTheme = resolveUITheme(brand?.uiTheme);
        this.#styleParents = styleParents;

        this.#customCSSStyleSheet = brand?.brandingCustomCss
            ? createStyleSheetUnsafe(brand.brandingCustomCss)
            : null;
    }

    #styleParents: StyleSheetParent[] = [];
    #customCSSStyleSheet: CSSStyleSheet | null;
    #darkThemeStyleSheet: CSSStyleSheet | null = null;

    #themeAbortController: AbortController | null = null;

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#themeAbortController?.abort();
    }

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        const renderRoot = super.createRenderRoot();

        const styleRoot = resolveStyleSheetParent(renderRoot);
        const styleParents = Array.from(
            new Set<StyleSheetParent>([styleRoot, ...this.#styleParents]),
        );

        if (this.#customCSSStyleSheet) {
            console.debug(`authentik/element[${this.tagName.toLowerCase()}]: Adding custom CSS`);

            styleRoot.adoptedStyleSheets = [
                ...styleRoot.adoptedStyleSheets,
                this.#customCSSStyleSheet,
            ];
        }

        this.#themeAbortController = new AbortController();

        createUIThemeEffect(
            (currentUITheme) => {
                if (currentUITheme === UiThemeEnum.Dark) {
                    this.#darkThemeStyleSheet ||= createStyleSheetUnsafe(ThemeDark);

                    appendStyleSheet(this.#darkThemeStyleSheet, ...styleParents);
                } else if (this.#darkThemeStyleSheet) {
                    removeStyleSheet(this.#darkThemeStyleSheet, ...styleParents);
                    this.#darkThemeStyleSheet = null;
                }
                this.activeTheme = currentUITheme;
            },
            {
                signal: this.#themeAbortController.signal,
            },
        );

        return renderRoot;
    }
}
