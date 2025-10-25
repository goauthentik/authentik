import { globalAK } from "#common/global";
import { createCSSResult, createStyleSheetUnsafe, StyleRoot } from "#common/stylesheets";
import {
    $AKBase,
    applyUITheme,
    createUIThemeEffect,
    CSSColorSchemeValue,
    formatColorScheme,
    ResolvedUITheme,
    resolveUITheme,
} from "#common/theme";

import { UiThemeEnum } from "@goauthentik/api";

import { localized } from "@lit/localize";
import { CSSResult, CSSResultGroup, CSSResultOrNative, LitElement, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

export interface AKElementProps {
    activeTheme: ResolvedUITheme;
}

@localized()
export class AKElement extends LitElement implements AKElementProps {
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

        if (process.env.NODE_ENV === "development") {
            const updatedCallback = this.updated;

            this.updated = function (args: PropertyValues) {
                updatedCallback?.call(this, args);

                const unregisteredElements = this.renderRoot.querySelectorAll(":not(:defined)");

                if (!unregisteredElements.length) return;

                for (const element of unregisteredElements) {
                    console.debug("Unregistered custom element found in the DOM", element);
                }
                throw new TypeError(
                    `${unregisteredElements.length} unregistered custom elements found in the DOM. See console for details.`,
                );
            };
        }
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
        } else if (this.preferredColorScheme === "light") {
            applyUITheme(nextStyleRoot, UiThemeEnum.Light, this.#customCSSStyleSheet);
            this.activeTheme = UiThemeEnum.Light;
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

    protected hasSlotted(name: string | null) {
        const isNotNestedSlot = (start: Element) => {
            let node = start.parentNode;
            while (node && node !== this) {
                if (node instanceof Element && node.hasAttribute("slot")) {
                    return false;
                }
                node = node.parentNode;
            }
            return true;
        };

        // All child slots accessible from the component's LightDOM that match the request
        const allChildSlotRequests =
            typeof name === "string"
                ? [...this.querySelectorAll(`[slot="${name}"]`)]
                : [...this.children].filter((child) => {
                      const slotAttr = child.getAttribute("slot");
                      return !slotAttr || slotAttr === "";
                  });

        // All child slots accessible from the LightDom that match the request *and* are not nested
        // within another slotted element.
        return allChildSlotRequests.filter((node) => isNotNestedSlot(node)).length > 0;
    }

    //#endregion
}
