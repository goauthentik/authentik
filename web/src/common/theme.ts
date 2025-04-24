/**
 * @file Theme utilities.
 */
import { UIConfig } from "@goauthentik/common/ui/config";

import { Config, CurrentBrand, UiThemeEnum } from "@goauthentik/api";

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
 * Create an effect that runs
 *
 * @returns A cleanup function that removes the effect.
 */
export function createUIThemeEffect(
    effect: UIThemeListener,
    listenerOptions?: AddEventListenerOptions,
): () => void {
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

    return cleanup;
}

//#endregion

//#region Theme Element

/**
 * An element that can be themed.
 */
export interface ThemedElement extends HTMLElement {
    brand?: CurrentBrand;
    uiConfig?: UIConfig;
    config?: Config;
    activeTheme: ResolvedUITheme;
}

export function rootInterface<T extends ThemedElement = ThemedElement>(): T | null {
    const element = document.body.querySelector<T>("[data-ak-interface-root]");

    return element;
}

//#endregion
