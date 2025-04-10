/**
 * @file CSS color scheme utilities.
 */
import { UiThemeEnum } from "@goauthentik/api";

/**
 * Valid CSS color scheme values.
 *
 * @link {@link https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme | MDN}
 */
export type CSSColorSchemeValue = "dark" | "light" | "auto";

/**
 * Creates an event target for the given color scheme.
 */
export function createColorSchemeTarget(colorScheme: CSSColorSchemeValue): MediaQueryList {
    return window.matchMedia(`(prefers-color-scheme: ${colorScheme})`);
}

/**
 * Formats the given input into a valid CSS color scheme value.
 *
 * If the input is not provided, it defaults to "auto".
 */
export function formatColorScheme(input?: CSSColorSchemeValue | UiThemeEnum): CSSColorSchemeValue {
    switch (input) {
        case UiThemeEnum.Dark:
        case "dark":
            return "dark";
        case UiThemeEnum.Light:
        case "light":
            return "light";
        default:
            return "auto";
    }
}

/**
 * Resolve the color scheme based on the user's preference or the provided color scheme.
 */
export function resolveColorScheme(
    colorSchemeHint?: CSSColorSchemeValue | UiThemeEnum,
): CSSColorSchemeValue {
    const colorScheme = formatColorScheme(colorSchemeHint);

    if (colorScheme !== "auto") return colorScheme;

    // Does the user-agent prefer a dark color scheme?
    const mediaQueryList = createColorSchemeTarget("dark");

    return mediaQueryList.matches ? "dark" : "light";
}

export interface ColorSchemeEffectInit {
    colorScheme: Exclude<CSSColorSchemeValue, "auto">;
    signal: AbortSignal;
}

/**
 * Create an effect that applies a given theme when the user-agent prefers a given color scheme.
 *
 * @returns A cleanup function that removes the effect.
 */
export function createColorSchemeEffect(
    { colorScheme, signal }: ColorSchemeEffectInit,
    effect: (matchesColorScheme: boolean) => void,
): () => void {
    // First, wrap the effect to ensure we can abort it.
    const changeListener = (event: MediaQueryListEvent) => {
        if (signal.aborted) return;

        effect(event.matches);
    };

    const cleanup = () => {
        mediaQueryList.removeEventListener("change", changeListener);
    };

    const mediaQueryList = createColorSchemeTarget(colorScheme);

    mediaQueryList.addEventListener("change", changeListener, {
        signal,
    });

    // Trigger the effect immediately.
    effect(mediaQueryList.matches);

    // Return the cleanup function.
    return cleanup;
}
