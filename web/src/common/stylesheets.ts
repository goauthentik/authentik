/**
 * @file Stylesheet utilities.
 */
import { CSSResult, CSSResultOrNative, ReactiveElement, css } from "lit";

/**
 * Elements containing adoptable stylesheets.
 */
export type StyleSheetParent = Pick<DocumentOrShadowRoot, "adoptedStyleSheets">;

/**
 * Type-predicate to determine if a given object has adoptable stylesheets.
 */
export function isAdoptableStyleSheetParent(input: unknown): input is StyleSheetParent {
    // Sanity check - Does the input have the right shape?

    if (!input || typeof input !== "object") return false;

    if (!("adoptedStyleSheets" in input) || !input.adoptedStyleSheets) return false;

    if (typeof input.adoptedStyleSheets !== "object") return false;

    // We avoid `Array.isArray` because the adopted stylesheets property
    // is defined as a proxied array.
    // All we care about is that it's shaped like an array.
    if (!("length" in input.adoptedStyleSheets)) return false;

    if (typeof input.adoptedStyleSheets.length !== "number") return false;

    // Finally is the array mutable?
    return "push" in input.adoptedStyleSheets;
}

/**
 * Assert that the given input can adopt stylesheets.
 */
export function assertAdoptableStyleSheetParent<T>(
    input: T,
): asserts input is T & StyleSheetParent {
    if (isAdoptableStyleSheetParent(input)) return;

    console.debug("Given input missing `adoptedStyleSheets`", input);

    throw new TypeError("Assertion failed: `adoptedStyleSheets` missing in given input");
}

export function resolveStyleSheetParent<T extends HTMLElement | DocumentFragment | Document>(
    renderRoot: T,
) {
    const styleRoot = "ShadyDOM" in window ? document : renderRoot;

    assertAdoptableStyleSheetParent(styleRoot);

    return styleRoot;
}

export type StyleSheetInit = string | CSSResult | CSSStyleSheet;

/**
 * Given a source of CSS, create a `CSSStyleSheet`.
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
 */
export function createStyleSheet(input: string): CSSResult {
    const inputTemplate = [input] as unknown as TemplateStringsArray;

    const result = css(inputTemplate, []);

    return result;
}

/**
 * Given a source of CSS, create a `CSSStyleSheet`.
 *
 * @see {@linkcode createStyleSheet}
 */
export function normalizeCSSSource(css: string): CSSStyleSheet;
export function normalizeCSSSource(styleSheet: CSSStyleSheet): CSSStyleSheet;
export function normalizeCSSSource(cssResult: CSSResult): CSSResult;
export function normalizeCSSSource(input: StyleSheetInit): CSSResultOrNative;
export function normalizeCSSSource(input: StyleSheetInit): CSSResultOrNative {
    if (typeof input === "string") return createStyleSheet(input);

    return input;
}

/**
 * Create a `CSSStyleSheet` from the given input.
 */
export function createStyleSheetUnsafe(input: StyleSheetInit): CSSStyleSheet {
    const result = normalizeCSSSource(input);
    if (result instanceof CSSStyleSheet) return result;

    if (!result.styleSheet) {
        console.debug(
            "authentik/common/stylesheets: CSSResult missing styleSheet, returning empty",
            { result, input },
        );

        throw new TypeError("Expected a CSSStyleSheet");
    }

    return result.styleSheet;
}

/**
 * Append stylesheet(s) to the given roots.
 *
 * @see {@linkcode removeStyleSheet} to remove a stylesheet from a given roots.
 */
export function appendStyleSheet(
    styleParent: StyleSheetParent,
    ...insertions: CSSStyleSheet[]
): void {
    insertions = Array.isArray(insertions) ? insertions : [insertions];

    for (const styleSheetInsertion of insertions) {
        if (styleParent.adoptedStyleSheets.includes(styleSheetInsertion)) return;

        styleParent.adoptedStyleSheets = [...styleParent.adoptedStyleSheets, styleSheetInsertion];
    }
}

/**
 * Remove a stylesheet from the given roots, matching by referential equality.
 *
 * @see {@linkcode appendStyleSheet} to append a stylesheet to a given roots.
 */
export function removeStyleSheet(
    styleParent: StyleSheetParent,
    ...removals: CSSStyleSheet[]
): void {
    const nextAdoptedStyleSheets = styleParent.adoptedStyleSheets.filter(
        (styleSheet) => !removals.includes(styleSheet),
    );

    if (nextAdoptedStyleSheets.length === styleParent.adoptedStyleSheets.length) return;

    styleParent.adoptedStyleSheets = nextAdoptedStyleSheets;
}

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
export function inspectStyleSheets(styleParent: StyleSheetParent): string[] {
    return styleParent.adoptedStyleSheets.map((styleSheet) => serializeStyleSheet(styleSheet));
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
    const styleParent = resolveStyleSheetParent(element.renderRoot);
    const styles = inspectStyleSheets(styleParent);
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

        if (!isAdoptableStyleSheetParent(childElement.renderRoot)) {
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
