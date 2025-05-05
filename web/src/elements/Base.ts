import { globalAK } from "@goauthentik/common/global";
import {
    StyleSheetInit,
    StyleSheetParent,
    appendStyleSheet,
    createStyleSheetUnsafe,
    removeStyleSheet,
    resolveStyleSheetParent,
} from "@goauthentik/common/stylesheets";
import {
    CSSColorSchemeValue,
    ResolvedUITheme,
    UIThemeListener,
    createUIThemeEffect,
    formatColorScheme,
    resolveUITheme,
} from "@goauthentik/common/theme";
import { type ThemedElement } from "@goauthentik/common/theme";

import { localized } from "@lit/localize";
import { CSSResultGroup, CSSResultOrNative, LitElement } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import OneDark from "@goauthentik/common/styles/one-dark.css";
import ThemeDark from "@goauthentik/common/styles/theme-dark.css";

import { UiThemeEnum } from "@goauthentik/api";

// Re-export the theme helpers
export { rootInterface } from "@goauthentik/common/theme";

@localized()
export class AKElement extends LitElement implements ThemedElement {
    //#region Properties

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

    //#endregion

    //#region Private Properties

    readonly #preferredColorScheme: CSSColorSchemeValue;

    #customCSSStyleSheet: CSSStyleSheet | null;
    #darkThemeStyleSheet: CSSStyleSheet | null = null;
    #themeAbortController: AbortController | null = null;

    //#endregion

    //#region Lifecycle

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

    constructor() {
        super();

        const { brand } = globalAK();

        this.#preferredColorScheme = formatColorScheme(brand.uiTheme);
        this.activeTheme = resolveUITheme(brand?.uiTheme);

        this.#customCSSStyleSheet = brand?.brandingCustomCss
            ? createStyleSheetUnsafe(brand.brandingCustomCss)
            : null;
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#themeAbortController?.abort();
    }

    #styleRoot?: StyleSheetParent;

    #dispatchTheme: UIThemeListener = (nextUITheme) => {
        if (!this.#styleRoot) return;

        if (nextUITheme === UiThemeEnum.Dark) {
            this.#darkThemeStyleSheet ||= createStyleSheetUnsafe(ThemeDark);
            appendStyleSheet(this.#styleRoot, this.#darkThemeStyleSheet);
            this.activeTheme = UiThemeEnum.Dark;
        } else if (this.#darkThemeStyleSheet) {
            removeStyleSheet(this.#styleRoot, this.#darkThemeStyleSheet);
            this.#darkThemeStyleSheet = null;
            this.activeTheme = UiThemeEnum.Light;
        }
    };

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        const renderRoot = super.createRenderRoot();
        this.#styleRoot = resolveStyleSheetParent(renderRoot);

        if (this.#customCSSStyleSheet) {
            console.debug(`authentik/element[${this.tagName.toLowerCase()}]: Adding custom CSS`);

            appendStyleSheet(this.#styleRoot, this.#customCSSStyleSheet);
        }

        this.#themeAbortController = new AbortController();

        if (this.#preferredColorScheme === "dark") {
            this.#dispatchTheme(UiThemeEnum.Dark);
        } else if (this.#preferredColorScheme === "auto") {
            createUIThemeEffect(this.#dispatchTheme, {
                signal: this.#themeAbortController.signal,
            });
        }

        return renderRoot;
    }

    //#endregion
}
