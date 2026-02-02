/**
 * @file Theme utilities.
 */

import { setAdoptedStyleSheets, type StyleRoot } from "#common/stylesheets";

import { UiThemeEnum } from "@goauthentik/api";

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
export function formatColorScheme(hint?: string): CSSColorSchemeValue;
export function formatColorScheme(hint?: string): CSSColorSchemeValue {
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
    hint?: string,
    defaultUITheme: ResolvedUITheme = UiThemeEnum.Light,
): ResolvedUITheme {
    const colorScheme = formatColorScheme(hint);

    if (colorScheme !== "auto") {
        return colorScheme;
    }

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
export type UIThemeListener = (currentUITheme: ResolvedUITheme, doc?: Document) => void;

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
    const colorSchemeTarget: ResolvedUITheme = "light";
    const inversionTarget = UIThemeInversion[colorSchemeTarget];

    const mediaQueryList = createColorSchemeTarget(colorSchemeTarget);

    // First, wrap the effect to ensure we can abort it.
    const mediaChangeListener = (event: MediaQueryListEvent) => {
        if (listenerOptions?.signal?.aborted) return;

        const { themeChoice, theme: previousTheme } = document.documentElement.dataset;

        if (themeChoice && themeChoice !== "auto") {
            console.debug(
                `authentik/theme (document): skipping media query change due to explicit choice (${themeChoice})`,
            );
            return;
        }

        const currentUITheme = event.matches ? colorSchemeTarget : inversionTarget;

        if (previousTheme === currentUITheme) return;

        effect(currentUITheme);
    };

    const themeChoiceListener = () => {
        let theme = formatColorScheme(document.documentElement.dataset.themeChoice);

        if (theme === "auto") {
            theme = mediaQueryList.matches
                ? colorSchemeTarget
                : UIThemeInversion[colorSchemeTarget];
        }

        document.documentElement.dataset.theme = theme;

        effect(theme);
    };

    const documentObserver = new MutationObserver(themeChoiceListener);

    documentObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme-choice"],
    });

    // Listen for changes to the color scheme...
    mediaQueryList.addEventListener("change", mediaChangeListener);

    // Finally, allow the caller to remove the effect.
    const cleanup = () => {
        documentObserver.disconnect();
        mediaQueryList.removeEventListener("change", mediaChangeListener);
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
    ...additionalStyleSheets: Array<CSSStyleSheet | undefined | null>
): void {
    setAdoptedStyleSheets(styleRoot, (currentStyleSheets) => {
        const appendedSheets = additionalStyleSheets.filter(Boolean) as CSSStyleSheet[];

        return [...currentStyleSheets, ...appendedSheets];
    });
}

export class ThemeChangeEvent extends Event {
    static readonly eventName = "ak-theme-change";

    public readonly theme: ResolvedUITheme;

    constructor(hint?: string) {
        super(ThemeChangeEvent.eventName, { bubbles: true, composed: true });

        this.theme = resolveUITheme(hint);
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [ThemeChangeEvent.eventName]: ThemeChangeEvent;
    }
}

/**
 * Applies the given theme to the document, i.e. the `<html>` element.
 *
 * @param hint The color scheme hint to use.
 * @param doc The document to apply the theme to.
 */
export const applyDocumentTheme = ((currentUITheme = resolveUITheme(), doc = document): void => {
    console.debug(`authentik/theme (document): want to switch to ${currentUITheme} theme`);

    const { themeChoice } = doc.documentElement.dataset;

    if (themeChoice && themeChoice !== "auto") {
        console.debug(
            `authentik/theme (document): skipping theme application due to explicit choice (${themeChoice})`,
        );

        doc.dispatchEvent(new ThemeChangeEvent(themeChoice));

        return;
    }

    doc.documentElement.dataset.theme = currentUITheme;

    console.debug(`authentik/theme (document): switching to ${currentUITheme} theme`);

    doc.dispatchEvent(new ThemeChangeEvent(currentUITheme));
}) satisfies UIThemeListener;

/**
 * Applies the given theme choice to the document element.
 *
 * @param hint The theme choice hint to apply.
 * @param documentElement The document element to apply the theme choice to.
 *
 * @remarks
 * There are a few scenarios that this function covers:
 *
 * - No hint, `"auto"` (via a media query), or `"automatic"` (via a user attribute)
 * - `"dark"` or `"light"` (explicit user choice)
 *
 * This may appear redundantly defensive when following this logic through the codebase.
 * However, there are some cases that only appear in development, such as...
 *
 * - The developer tools overriding the system color scheme
 * - The attribute is manually changed to an invalid value
 */
export function applyThemeChoice(hint?: CSSColorSchemeValue, doc: Document = document): void {
    const themeChoice = !hint || hint === "auto" ? "auto" : resolveUITheme(hint);

    doc.documentElement.dataset.themeChoice = themeChoice;
}

/**
 * A CSS variable representing the global background image.
 */
export const AKBackgroundImageProperty = "--ak-global--background-image";

/**
 * Given a CSS background-image property value, plucks the URL from it.
 *
 * @param backgroundValue The CSS background-image property value.
 * @param baseOrigin The base origin to use for relative URLs.
 * @returns The plucked URL, if any.
 */
function pluckCurrentBackgroundURL(
    backgroundValue: string,
    baseOrigin = window.location.origin,
): URL | null {
    if (!backgroundValue || backgroundValue === "none") {
        return null;
    }

    const match = backgroundValue.match(/url\(["']?([^"']*)["']?\)/);
    const urlString = match?.[1];

    if (urlString && URL.canParse(urlString, baseOrigin)) {
        return new URL(urlString, baseOrigin);
    }

    return null;
}

export interface BackgroundImageInit {
    baseOrigin?: string;
    target?: HTMLElement | null;
}

/**
 * Applies the given background image URL to the document body.
 *
 * This method is very defensive to avoid unnecessary DOM repaints.
 */
export function applyBackgroundImageProperty(
    value?: string | null,
    init?: BackgroundImageInit,
): void {
    const baseOrigin = init?.baseOrigin ?? window.location.origin;

    if (!value || !URL.canParse(value, baseOrigin)) {
        return;
    }

    const target = init?.target ?? document.body;

    const nextURL = new URL(value, baseOrigin);

    const { backgroundImage } = getComputedStyle(target, "::before");

    const currentURL = pluckCurrentBackgroundURL(backgroundImage, baseOrigin);
    if (currentURL?.href === nextURL.href) {
        return;
    }

    target.style.setProperty(AKBackgroundImageProperty, `url("${nextURL.href}")`);
}

/**
 * Returns the root interface element of the page.
 *
 * @deprecated Use context controllers to access the interface root instead.
 */
export function rootInterface<T extends HTMLElement = HTMLElement>(): T {
    const element = document.body.querySelector<T>("[data-test-id=interface-root]");

    if (!element) {
        throw new Error(
            `Could not find root interface element. Was this element added before the parent interface element?`,
        );
    }

    return element;
}

//#endregion
