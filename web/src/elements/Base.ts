import { globalAK } from "#common/global";
import { StyleRoot, createCSSResult, createStyleSheetUnsafe } from "#common/stylesheets";
import {
    $AKBase,
    CSSColorSchemeValue,
    ResolvedUITheme,
    applyUITheme,
    createUIThemeEffect,
    formatColorScheme,
    resolveUITheme,
} from "#common/theme";

import { localized } from "@lit/localize";
import { CSSResult, CSSResultGroup, CSSResultOrNative, LitElement } from "lit";
import { property } from "lit/decorators.js";

import { UiThemeEnum } from "@goauthentik/api";

@localized()
export class AKElement extends LitElement {
    //#region Static Properties

    public static styles?: Array<CSSResult | CSSModule>;

    protected static override finalizeStyles(styles?: CSSResultGroup): CSSResultOrNative[] {
        if (!styles) return [$AKBase];

        if (!Array.isArray(styles)) return [createCSSResult(styles), $AKBase];

        return [
            // ---
            ...(styles.flat() as CSSResultOrNative[]).map(createCSSResult),
            $AKBase,
        ];
    }

    //#endregion

    //#region Lifecycle

    constructor() {
        super();

        const { brand } = globalAK();

        this.preferredColorScheme = formatColorScheme(brand.uiTheme);
        this.activeTheme = resolveUITheme(brand?.uiTheme);

        this.#customCSSStyleSheet = brand?.brandingCustomCss
            ? createStyleSheetUnsafe(brand.brandingCustomCss)
            : null;
    }

    public override disconnectedCallback(): void {
        this.#themeAbortController?.abort();
        super.disconnectedCallback();
    }

    /**
     * Returns the node into which the element should render.
     *
     * @see {LitElement.createRenderRoot} for more information.
     */
    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        const renderRoot = super.createRenderRoot();
        this.styleRoot ??= renderRoot;

        return renderRoot;
    }

    //#endregion

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

    /**
     * The preferred color scheme used to look up the UI theme.
     */
    protected readonly preferredColorScheme: CSSColorSchemeValue;

    /**
     * A custom CSS style sheet to apply to the element.
     */
    readonly #customCSSStyleSheet: CSSStyleSheet | null;

    /**
     * A controller to abort theme updates, such as when the element is disconnected.
     */
    #themeAbortController: AbortController | null = null;
    /**
     * The style root to which the theme is applied.
     */
    #styleRoot?: StyleRoot;

    protected set styleRoot(nextStyleRoot: StyleRoot | undefined) {
        this.#themeAbortController?.abort();

        this.#styleRoot = nextStyleRoot;

        if (!nextStyleRoot) return;

        this.#themeAbortController = new AbortController();

        if (this.preferredColorScheme === "dark") {
            applyUITheme(nextStyleRoot, UiThemeEnum.Dark, this.#customCSSStyleSheet);

            this.activeTheme = UiThemeEnum.Dark;
        } else if (this.preferredColorScheme === "auto") {
            createUIThemeEffect(
                (nextUITheme) => {
                    applyUITheme(nextStyleRoot, nextUITheme, this.#customCSSStyleSheet);

                    this.activeTheme = nextUITheme;
                },
                {
                    signal: this.#themeAbortController.signal,
                },
            );
        }
    }

    protected get styleRoot(): StyleRoot | undefined {
        return this.#styleRoot;
    }

    //#endregion
}
