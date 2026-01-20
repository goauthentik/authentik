import { globalAK } from "#common/global";
import { createCSSResult, createStyleSheetUnsafe, StyleRoot } from "#common/stylesheets";
import { applyUITheme, ResolvedUITheme, resolveUITheme, ThemeChangeEvent } from "#common/theme";

import AKBase from "#styles/authentik/base.css" with { type: "bundled-text" };
import PFBase from "#styles/patternfly/base.css" with { type: "bundled-text" };

import { localized } from "@lit/localize";
import { CSSResult, CSSResultGroup, CSSResultOrNative, LitElement, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

/**
 * Patternfly base styles, providing common variables and resets.
 *
 * @remarks
 *
 * This style sheet **must** be included before any other styles that depend on Patternfly variables.
 */
const $PFBase = createStyleSheetUnsafe(PFBase);

/**
 * authentik base styles, providing overrides to Patternfly's initial definitions,
 * and additional customizations.
 */
const $AKBase = createStyleSheetUnsafe(AKBase);

export interface AKElementProps {
    activeTheme: ResolvedUITheme;
}

@localized()
export class AKElement extends LitElement implements AKElementProps {
    //#region Static Properties

    public static styles?: Array<CSSResult | CSSModule>;

    protected static override finalizeStyles(styles: CSSResultGroup = []): CSSResultOrNative[] {
        const elementStyles = [
            $PFBase,
            // Route around TSC`s known-to-fail typechecking of `.flat(Infinity)`. Removes types.
            ...([styles] as Array<unknown>).flat(Infinity),
            $AKBase,
            // Restore types. Safe: we control AKBase and PFBase in this file, and `styles` are
            // typed on function signature.
        ] as CSSResultOrNative[];

        // Remove duplicates in reverse order to preserve last-insert-wins semantics of CSS.
        const elementSet = new Set(elementStyles.reverse());
        // Reverse again because the return type is an array, and process as a CSSResult
        return Array.from(elementSet).reverse().map(createCSSResult);
    }

    //#endregion

    //#region Lifecycle

    constructor() {
        super();

        const { brand } = globalAK();

        const preferredColorScheme = resolveUITheme(
            document.documentElement.dataset.theme || globalAK().brand.uiTheme,
        );
        this.activeTheme = preferredColorScheme;

        this.#customCSSStyleSheet = brand?.brandingCustomCss
            ? createStyleSheetUnsafe(brand.brandingCustomCss)
            : null;

        if (process.env.NODE_ENV === "development") {
            const updatedCallback = this.updated;

            this.updated = function updatedWrapper(args: PropertyValues) {
                updatedCallback?.call(this, args);

                const unregisteredElements = this.renderRoot.querySelectorAll(
                    `:not(:defined):not([data-registration="lazy"])`,
                );

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

        document.addEventListener(
            ThemeChangeEvent.eventName,
            (event) => {
                applyUITheme(nextStyleRoot, this.#customCSSStyleSheet);

                this.activeTheme = event.theme;
            },
            {
                signal: this.#themeAbortController.signal,
            },
        );
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
