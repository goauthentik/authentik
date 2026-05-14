import { globalAK } from "#common/global";
import {
    createCSSResult,
    createStyleSheetUnsafe,
    setAdoptedStyleSheets,
    StyleRoot,
} from "#common/stylesheets";
import { applyUITheme, ResolvedUITheme, resolveUITheme, ThemeChangeEvent } from "#common/theme";

import AKBase from "#styles/authentik/base.css" with { type: "bundled-text" };
import PFBase from "#styles/patternfly/base.css" with { type: "bundled-text" };

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

export class AKElement extends LitElement implements AKElementProps {
    //#region Static Properties

    public static styles?: Array<CSSResult | CSSModule>;

    /**
     * Host styles are styles that are applied to the element's render root,
     * but are not scoped to the element itself.
     *
     * @remarks
     *
     * This is useful if the element is a wrapper around a third-party component
     * that requires styles to be applied to the host, such as Patternfly's modals.
     */
    public static get hostStyles(): CSSResultOrNative[] {
        return this.hostStyleSheets ?? [];
    }

    public static set hostStyles(styles: CSSResultOrNative[]) {
        this.hostStyleSheets = styles.map(createStyleSheetUnsafe);
    }

    /**
     * A cache of the element's host styles, converted to {@linkcode CSSStyleSheet}
     * instances to avoid duplicated references.
     *
     * **You should not need to interact with this property directly.**
     *
     * @see {@linkcode hostStyles} for the public API for this property.
     *
     * @protected
     */
    protected static hostStyleSheets: CSSStyleSheet[] | null = null;

    protected static override finalizeStyles(styles: CSSResultGroup = []): CSSResultOrNative[] {
        const elementStyles = [
            $PFBase,
            // Route around TSC`s known-to-fail typechecking of `.flat(Infinity)`. Removes types.
            ...([styles] as Array<unknown>).flat(Infinity),
            $AKBase,
            // Restore types. Safe: we control AKBase and PFBase in this file, and `styles` are
            // typed on function signature.
        ] as CSSResultOrNative[];

        // Remove duplicates in reverse order to preserve last-insert-wins semantics of CSS. See:
        // https://github.com/lit/lit/blob/main/packages/reactive-element/src/reactive-element.ts#L945
        const elementSet = new Set(elementStyles.reverse());
        // Reverse again because the return type is an array, and process as a CSSResult
        return Array.from(elementSet).reverse().map(createCSSResult);
    }

    protected static attachHostStyles(rootNode: StyleRoot): void {
        const { hostStyleSheets } = this;

        if (!hostStyleSheets) return;

        setAdoptedStyleSheets(rootNode, (currentStyleSheets) => {
            return [...currentStyleSheets, ...hostStyleSheets];
        });
    }

    protected static detachHostStyles(rootNode: StyleRoot): void {
        const { hostStyleSheets } = this;

        if (!hostStyleSheets) return;

        setAdoptedStyleSheets(rootNode, (currentStyleSheets) => {
            return currentStyleSheets.filter((sheet) => !hostStyleSheets.includes(sheet));
        });
    }

    //#endregion

    //#region Lifecycle

    constructor() {
        super();

        const { brand } = globalAK();

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

    public override connectedCallback(): void {
        super.connectedCallback();

        if (this.renderRoot !== this) {
            property({
                attribute: "theme",
                type: String,
                reflect: true,
            })(this, "activeTheme");

            const hint =
                this.ownerDocument.documentElement.dataset.theme || globalAK().brand.uiTheme;
            const preferredColorScheme = resolveUITheme(hint);

            this.activeTheme = preferredColorScheme;
        }

        const rootNode = this.getRootNode();

        if (rootNode instanceof ShadowRoot || rootNode instanceof Document) {
            (this.constructor as typeof AKElement).attachHostStyles(rootNode);
        }
    }

    public override disconnectedCallback(): void {
        this.#themeAbortController?.abort();

        const rootNode = this.getRootNode();

        if (rootNode instanceof ShadowRoot) {
            (this.constructor as typeof AKElement).detachHostStyles(rootNode);
        }

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
     * This property is lazy-initialized when the element is connected.
     *
     * Unlike the browser's current color scheme, this is a value that can be
     * resolved to a specific theme, i.e. dark or light.
     *
     * @attr ("light" | "dark") activeTheme
     */
    public activeTheme!: ResolvedUITheme;

    //#endregion

    //#region Private Properties

    /**
     * A custom CSS style sheet to apply to the element.
     *
     * @deprecated Use CSS parts and custom properties instead.
     *
     * @remarks
     * The use of injected style sheets may result in brittle styles that are hard to
     * maintain across authentik versions.
     *
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

    /**
     * The style root to which the theme is applied.
     */
    protected get styleRoot(): StyleRoot | undefined {
        return this.#styleRoot;
    }

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

        if (this.#customCSSStyleSheet) {
            applyUITheme(nextStyleRoot, this.#customCSSStyleSheet);
        }
    }

    /**
     * Finds a slotted element by name, ensuring that it is not nested within another slotted element.
     *
     * @param slotName The name of the slot to find. Omit to find elements in the default slot.
     * @return The slotted element, or `null` if no matching element is found.
     */
    protected findSlotted<T extends Element = Element>(slotName?: string): T | null {
        const isNotNestedSlot = (start: Element) => {
            let node = start.parentNode;

            while (node && node !== this) {
                if (node instanceof Element && node.hasAttribute("slot")) {
                    return null;
                }
                node = node.parentNode;
            }

            return node;
        };

        // All child slots accessible from the component's LightDOM that match the request
        const allChildSlotRequests =
            typeof slotName === "string"
                ? [...this.querySelectorAll(`[slot="${slotName}"]`)]
                : [...this.children].filter((child) => {
                      const slotAttr = child.getAttribute("slot");
                      return !slotAttr || slotAttr === "";
                  });

        // All child slots accessible from the LightDom that match the request *and* are not nested
        // within another slotted element.
        const match = allChildSlotRequests.find((node) => isNotNestedSlot(node));

        return (match ?? null) as T | null;
    }

    //#endregion
}
