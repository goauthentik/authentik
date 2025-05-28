/**
 * @file Theme utilities.
 */
import { type StyleRoot, createStyleSheetUnsafe, setAdoptedStyleSheets } from "#common/stylesheets";

import AKBase from "#common/styles/authentik.css";
import AKBaseDark from "#common/styles/theme-dark.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { UiThemeEnum } from "@goauthentik/api";

//#region Stylesheet Exports

/**
 * A global style sheet for the Patternfly base styles.
 *
 * @remarks
 *
 * While a component *may* import its own instance of the PFBase style sheet,
 * this instance ensures referential identity.
 */
export const $PFBase = createStyleSheetUnsafe(PFBase);

/**
 * A global style sheet for the authentik base styles.
 *
 * @see {@linkcode $PFBase} for details.
 */
export const $AKBase = createStyleSheetUnsafe(AKBase);

/**
 * A global style sheet for the authentik dark theme.
 *
 * @see {@linkcode $PFBase} for details.
 */
export const $AKBaseDark = createStyleSheetUnsafe(AKBaseDark);

//#endregion

//#region Scheme Types

/**
 * Valid CSS color scheme values.
 *
 * @link {@link https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme | MDN}
 *
 * @category CSS
 */
export type CSSColorSchemeValue = "dark" | "light" | "auto";

/**
 * A CSS color scheme value that can be preferred by the user, i.e. not `"auto"`.
 *
 * @category CSS
 */
export type ResolvedCSSColorSchemeValue = Exclude<CSSColorSchemeValue, "auto">;

//#endregion

//#region UI Theme Types

/**
 * A UI color scheme value that can be preferred by the user.
 *
 * i.e. not an lack of preference or unknown value.
 *
 * @category CSS
 */
export type ResolvedUITheme = typeof UiThemeEnum.Light | typeof UiThemeEnum.Dark;

/**
 * A mapping of theme values to their respective inversion.
 *
 * @category CSS
 */
export const UIThemeInversion = {
    dark: "light",
    light: "dark",
} as const satisfies Record<ResolvedUITheme, ResolvedUITheme>;

/**
 * Either a valid CSS color scheme value, or a theme preference.
 */
export type UIThemeHint = CSSColorSchemeValue | UiThemeEnum;

//#endregion

//#region Scheme Functions

/**
 * Creates an event target for the given color scheme.
 *
 * @param colorScheme The color scheme to target.
 * @returns A {@linkcode MediaQueryList} that can be used to listen for changes to the color scheme.
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/MediaQueryList | MDN}
 *
 * @category CSS
 */
export function createColorSchemeTarget(colorScheme: ResolvedCSSColorSchemeValue): MediaQueryList {
    return window.matchMedia(`(prefers-color-scheme: ${colorScheme})`);
}

/**
 * Formats the given input into a valid CSS color scheme value.
 *
 * If the input is not provided, it defaults to "auto".
 *
 * @category CSS
 */
export function formatColorScheme(theme: ResolvedUITheme): ResolvedCSSColorSchemeValue;
export function formatColorScheme(
    colorScheme: ResolvedCSSColorSchemeValue,
): ResolvedCSSColorSchemeValue;
export function formatColorScheme(hint?: UIThemeHint): CSSColorSchemeValue;
export function formatColorScheme(hint?: UIThemeHint): CSSColorSchemeValue {
    if (!hint) return "auto";

    switch (hint) {
        case "dark":
        case UiThemeEnum.Dark:
            return "dark";
        case "light":
        case UiThemeEnum.Light:
            return "light";
        case "auto":
        case UiThemeEnum.Automatic:
            return "auto";
        default:
            console.warn(`Unknown color scheme hint: ${hint}. Defaulting to "auto".`);
            return "auto";
    }
}

//#endregion

//#region Theme Functions

/**
 * Resolve the current UI theme based on the user's preference or the provided color scheme.
 *
 * @param hint The color scheme hint to use.
 *
 * @category CSS
 */
export function resolveUITheme(
    hint?: UIThemeHint,
    defaultUITheme: ResolvedUITheme = UiThemeEnum.Light,
): ResolvedUITheme {
    const colorScheme = formatColorScheme(hint);

    if (colorScheme !== "auto") return colorScheme;

    // Given that we don't know the user's preference,
    // we can determine the theme based on whether the default theme is
    // currently being overridden.

    const colorSchemeInversion = formatColorScheme(UIThemeInversion[defaultUITheme]);

    const mediaQueryList = createColorSchemeTarget(colorSchemeInversion);

    return mediaQueryList.matches ? colorSchemeInversion : defaultUITheme;
}

/**
 * Effect listener invoked when the color scheme changes.
 */
export type UIThemeListener = (currentUITheme: ResolvedUITheme) => void;

/**
 * Effect destructor invoked when cleanup is required.
 */
export type UIThemeDestructor = () => void;

/**
 * Create an effect that runs UI theme changes.
 *
 * @returns A cleanup function that removes the effect.
 */
export function createUIThemeEffect(
    effect: UIThemeListener,
    listenerOptions?: AddEventListenerOptions,
): UIThemeDestructor {
    const colorSchemeTarget = resolveUITheme();
    const invertedColorSchemeTarget = UIThemeInversion[colorSchemeTarget];

    let previousUITheme: ResolvedUITheme | undefined;

    // First, wrap the effect to ensure we can abort it.
    const changeListener = (event: MediaQueryListEvent) => {
        if (listenerOptions?.signal?.aborted) return;

        const currentUITheme = event.matches ? colorSchemeTarget : invertedColorSchemeTarget;

        if (previousUITheme === currentUITheme) return;

        previousUITheme = currentUITheme;

        effect(currentUITheme);
    };

    const mediaQueryList = createColorSchemeTarget(colorSchemeTarget);

    // Trigger the effect immediately.
    effect(colorSchemeTarget);

    // Listen for changes to the color scheme...
    mediaQueryList.addEventListener("change", changeListener, listenerOptions);

    // Finally, allow the caller to remove the effect.
    const cleanup = () => {
        mediaQueryList.removeEventListener("change", changeListener);
    };

    listenerOptions?.signal?.addEventListener("abort", cleanup);

    return cleanup;
}

//#endregion

//#region Theme Element

/**
 * Applies the current UI theme to the given style root.
 *
 * @param styleRoot The style root to apply the theme to.
 * @param currentUITheme The current UI theme to apply.
 * @param additionalStyleSheets Additional style sheets to apply, in addition to the theme's base sheets.
 * @category CSS
 *
 * @see {@linkcode setAdoptedStyleSheets} for caveats.
 */
export function applyUITheme(
    styleRoot: StyleRoot,
    currentUITheme: ResolvedUITheme = resolveUITheme(),
    ...additionalStyleSheets: Array<CSSStyleSheet | undefined | null>
): void {
    setAdoptedStyleSheets(styleRoot, (currentStyleSheets) => {
        const appendedSheets = additionalStyleSheets.filter(Boolean) as CSSStyleSheet[];

        if (currentUITheme === UiThemeEnum.Dark) {
            return [...currentStyleSheets, $AKBaseDark, ...appendedSheets];
        }

        return [
            ...currentStyleSheets.filter((styleSheet) => styleSheet !== $AKBaseDark),
            ...appendedSheets,
        ];
    });
}

/**
 * Applies the given theme to the document, i.e. the `<html>` element.
 *
 * @param hint The color scheme hint to use.
 */
export function applyDocumentTheme(hint: CSSColorSchemeValue | UIThemeHint = "auto"): void {
    const preferredColorScheme = formatColorScheme(hint);

    if (document.documentElement.dataset.theme === preferredColorScheme) return;

    const applyStyleSheets: UIThemeListener = (currentUITheme) => {
        console.debug(`authentik/theme (document): switching to ${currentUITheme} theme`);

        setAdoptedStyleSheets(document, (currentStyleSheets) => {
            if (currentUITheme === "dark") {
                return [...currentStyleSheets, $PFBase, $AKBase, $AKBaseDark];
            }

            return [
                ...currentStyleSheets.filter((styleSheet) => styleSheet !== $AKBaseDark),
                $PFBase,
                $AKBase,
            ];
        });

        document.documentElement.dataset.theme = currentUITheme;
    };

    if (preferredColorScheme === "auto") {
        createUIThemeEffect(applyStyleSheets);
        return;
    }

    applyStyleSheets(preferredColorScheme);
}

/**
 * Returns the root interface element of the page.
 *
 * @todo Can this be handled with a Lit Mixin?
 */
export function rootInterface<T extends HTMLElement = HTMLElement>(): T {
    const element = document.body.querySelector<T>("[data-ak-interface-root]");

    if (!element) {
        throw new Error(
            `Could not find root interface element. Was this element added before the parent interface element?`,
        );
    }

    return element;
}

//#endregion
