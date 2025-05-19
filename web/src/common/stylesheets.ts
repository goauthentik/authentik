/**
 * @file Stylesheet utilities.
 */
import { CSSResultOrNative, ReactiveElement, adoptStyles as adoptStyleSheetsShim, css } from "lit";

/**
 * Element-like objects containing adoptable stylesheets.
 *
 * Note that while these all possess the `adoptedStyleSheets` property,
 * browser differences and polyfills may make them not actually adoptable.
 *
 * This type exists to normalize the different ways of accessing the property.
 */
export type StyleRoot =
    | Document
    | ShadowRoot
    | DocumentFragment
    | HTMLElement
    | DocumentOrShadowRoot;

/**
 * Type-predicate to determine if a given object has adoptable stylesheets.
 */
export function isStyleRoot(input: StyleRoot): input is ShadowRoot {
    // Sanity check - Does the input have the right shape?

    if (!input || typeof input !== "object") return false;

    if (!("adoptedStyleSheets" in input) || !input.adoptedStyleSheets) return false;

    if (typeof input.adoptedStyleSheets !== "object") return false;

    // We avoid `Array.isArray` because the adopted stylesheets property
    // is defined as a proxied array.
    // All we care about is that it's shaped like an array.
    if (!("length" in input.adoptedStyleSheets)) return false;

    return typeof input.adoptedStyleSheets.length === "number";
}

/**
 * Create a lazy-loaded `CSSResult` compatible with Lit's
 * element lifecycle.
 *
 * @throw {@linkcode TypeError} if the input cannot be converted to a `CSSStyleSheet`
 *
 * @remarks
 *
 * Storybook's `build` does not currently have a coherent way of importing
 * CSS-as-text into CSSStyleSheet.
 *
 * It works well when Storybook is running in `dev`, but in `build` it fails.
 * Storied components will have to map their textual CSS imports.
 *
 * @see {@linkcode createStyleSheetUnsafe} to create a `CSSStyleSheet` from the given input.
 */
export function createCSSResult(input: string | CSSModule | CSSResultOrNative): CSSResultOrNative {
    if (typeof input !== "string") return input;

    const inputTemplate = [input] as unknown as TemplateStringsArray;

    const result = css(inputTemplate, []);

    return result;
}

/**
 * Create a `CSSStyleSheet` from the given input, if it is not already a `CSSStyleSheet`.
 *
 * @throw {@linkcode TypeError} if the input cannot be converted to a `CSSStyleSheet`
 *
 * @see {@linkcode createCSSResult} for the lazy-loaded `CSSResult` normalization.
 */
export function createStyleSheetUnsafe(
    input: string | CSSModule | CSSResultOrNative,
): CSSStyleSheet {
    const result = typeof input === "string" ? createCSSResult(input) : input;

    if (result instanceof CSSStyleSheet) return result;

    if (result.styleSheet) return result.styleSheet;

    const styleSheet = new CSSStyleSheet();

    styleSheet.replaceSync(result.cssText);

    return styleSheet;
}

export type StyleSheetsAction =
    | Iterable<CSSStyleSheet>
    | ((currentStyleSheets: CSSStyleSheet[]) => Iterable<CSSStyleSheet>);

/**
 * Set the adopted stylesheets of a given style parent.
 *
 * ```ts
 * setAdoptedStyleSheets(document.body, (currentStyleSheets) => [
 *     ...currentStyleSheets,
 *     myStyleSheet,
 * ]);
 * ```
 *
 * @remarks
 * Replacing `adoptedStyleSheets` more than once in the same frame may result in
 * the `currentStyleSheets` parameter being out of sync with the actual sheets.
 *
 * A style root's `adoptedStyleSheets` is a proxy object that only updates when
 * DOM is repainted. We can't easily cache the previous entries since the style root
 * may polyfilled via ShadyDOM.
 *
 * Short of using {@linkcode requestAnimationFrame} to sequence the adoption,
 * and a visibility toggle to avoid a flash of styles between renders,
 * we can't reliably cache the previous entries.
 *
 * In the meantime, we should try to apply all the sheets in a single frame.
 */
export function setAdoptedStyleSheets(styleRoot: StyleRoot, styleSheets: StyleSheetsAction): void {
    let changed = false;

    const currentAdoptedStyleSheets = isStyleRoot(styleRoot)
        ? [...styleRoot.adoptedStyleSheets]
        : [];

    const result =
        typeof styleSheets === "function" ? styleSheets(currentAdoptedStyleSheets) : styleSheets;

    const nextAdoptedStyleSheets: CSSStyleSheet[] = [];

    for (const [idx, styleSheet] of Array.from(result).entries()) {
        const previousStyleSheet = currentAdoptedStyleSheets[idx];

        changed ||= previousStyleSheet !== styleSheet;

        if (nextAdoptedStyleSheets.includes(styleSheet)) continue;

        nextAdoptedStyleSheets.push(styleSheet);
    }

    changed ||= nextAdoptedStyleSheets.length !== currentAdoptedStyleSheets.length;

    if (!changed) return;

    if (styleRoot === document) {
        document.adoptedStyleSheets = nextAdoptedStyleSheets;
        return;
    }

    adoptStyleSheetsShim(styleRoot as unknown as ShadowRoot, nextAdoptedStyleSheets);
}

//#region Debugging

/**
 * Serialize a stylesheet to a string.
 *
 * This is useful for debugging or inspecting the contents of a stylesheet.
 */
export function serializeStyleSheet(stylesheet: CSSStyleSheet): string {
    return Array.from(stylesheet.cssRules || [], (rule) => rule.cssText || "").join("\n");
}

/**
 * Inspect the adopted stylesheets of a given style parent, serializing them to strings.
 */
export function inspectStyleSheets(styleRoot: ShadowRoot): string[] {
    return styleRoot.adoptedStyleSheets.map((styleSheet) => serializeStyleSheet(styleSheet));
}

interface InspectedStyleSheetEntry {
    tagName: string;
    element: ReactiveElement;
    styles: string[];
    children?: InspectedStyleSheetEntry[];
}

/**
 * Recursively inspect the adopted stylesheets of a given style parent, serializing them to strings.
 */
export function inspectStyleSheetTree(element: ReactiveElement): InspectedStyleSheetEntry {
    if (!isStyleRoot(element.renderRoot)) {
        throw new TypeError("Cannot inspect a render root that doesn't have adoptable stylesheets");
    }

    const styles = inspectStyleSheets(element.renderRoot);
    const tagName = element.tagName.toLowerCase();

    const treewalker = document.createTreeWalker(element.renderRoot, NodeFilter.SHOW_ELEMENT, {
        acceptNode(node) {
            if (node instanceof ReactiveElement) {
                return NodeFilter.FILTER_ACCEPT;
            }
            return NodeFilter.FILTER_SKIP;
        },
    });

    const children: InspectedStyleSheetEntry[] = [];
    let currentNode: Node | null = treewalker.nextNode();

    while (currentNode) {
        const childElement = currentNode as ReactiveElement;

        if (!isStyleRoot(childElement.renderRoot)) {
            currentNode = treewalker.nextNode();
            continue;
        }

        const childStyles = inspectStyleSheets(childElement.renderRoot);

        children.push({
            tagName: childElement.tagName.toLowerCase(),
            element: childElement,
            styles: childStyles,
        });
        currentNode = treewalker.nextNode();
    }

    return {
        tagName,
        element,
        styles,
        children,
    };
}

if (process.env.NODE_ENV === "development") {
    Object.assign(window, {
        inspectStyleSheetTree,
        serializeStyleSheet,
        inspectStyleSheets,
    });
}

//#endregion
