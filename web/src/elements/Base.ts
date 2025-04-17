import {
    CSSColorSchemeValue,
    createColorSchemeEffect,
    resolveColorScheme,
} from "@goauthentik/common/color-scheme";
import { globalAK } from "@goauthentik/common/global";
import {
    StyleSheetInit,
    StyleSheetParent,
    appendStyleSheet,
    createStyleSheetUnsafe,
    removeStyleSheet,
    resolveStyleSheetParent,
} from "@goauthentik/common/stylesheets";
import { type ThemedElement } from "@goauthentik/elements/utils/theme";

import { localized } from "@lit/localize";
import { CSSResultGroup, CSSResultOrNative, LitElement } from "lit";
import { state } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import OneDark from "@goauthentik/common/styles/one-dark.css";
import ThemeDark from "@goauthentik/common/styles/theme-dark.css";

import { CurrentBrand } from "@goauthentik/api";

export interface AKElementInit {
    brand?: Partial<CurrentBrand>;
    styleParents?: StyleSheetParent[];
}

@localized()
export class AKElement extends LitElement implements ThemedElement {
    static readonly DarkColorSchemeStyleSheet = createStyleSheetUnsafe(ThemeDark);

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

        this.#styleParents = styleParents;

        this.#customCSSStyleSheet = brand?.brandingCustomCss
            ? createStyleSheetUnsafe(brand.brandingCustomCss)
            : null;

        this.colorScheme = resolveColorScheme(brand.uiTheme);
    }

    #styleParents: StyleSheetParent[] = [];
    #customCSSStyleSheet: CSSStyleSheet | null;

    @state()
    public colorScheme: CSSColorSchemeValue;
    readonly #colorSchemeAbortController = new AbortController();

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#colorSchemeAbortController.abort();
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

        createColorSchemeEffect(
            {
                colorScheme: "dark",
                signal: this.#colorSchemeAbortController.signal,
            },
            (matches) => {
                if (matches) {
                    appendStyleSheet(AKElement.DarkColorSchemeStyleSheet, ...styleParents);
                    this.colorScheme = "dark";
                    this.setAttribute("theme", "dark");
                } else {
                    removeStyleSheet(AKElement.DarkColorSchemeStyleSheet, ...styleParents);
                    this.colorScheme = "light";
                    this.setAttribute("theme", "light");
                }
            },
        );

        return renderRoot;
    }
}
