/**
 * @file CSS color scheme utilities.
 */

/**
 * Valid CSS color scheme values.
 *
 * @link {@link https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme | MDN}
 */
export type CSSColorSchemeValue = "dark" | "light" | "auto";

/**
 * A CSS color scheme value that can be preferred by the user, i.e. not `"auto"`.
 */
export type ResolvedCSSColorSchemeValue = Exclude<CSSColorSchemeValue, "auto">;

/**
 * A mapping of color scheme values to their inversion.
 */
export const ColorSchemeInversion = {
    dark: "light",
    light: "dark",
} as const satisfies Record<ResolvedCSSColorSchemeValue, ResolvedCSSColorSchemeValue>;

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
export function formatColorScheme(input?: CSSColorSchemeValue): CSSColorSchemeValue {
    switch (input) {
        case "dark":
            return "dark";
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
    colorSchemeHint?: CSSColorSchemeValue,
): ResolvedCSSColorSchemeValue {
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

export type ColorSchemeEffectListener = (
    matchesColorScheme: boolean,
    currentColorScheme: ResolvedCSSColorSchemeValue,
) => void;
/**
 * Create an effect that applies a given theme when the user-agent prefers a given color scheme.
 *
 * @returns A cleanup function that removes the effect.
 */
export function createColorSchemeEffect(
    { colorScheme, signal }: ColorSchemeEffectInit,
    effect: ColorSchemeEffectListener,
): () => void {
    let previousColorScheme: ResolvedCSSColorSchemeValue | undefined;

    // First, wrap the effect to ensure we can abort it.
    const changeListener = (event: MediaQueryListEvent) => {
        if (signal.aborted) return;

        const currentColorScheme = event.matches ? colorScheme : ColorSchemeInversion[colorScheme];

        if (previousColorScheme === currentColorScheme) return;

        previousColorScheme = currentColorScheme;

        effect(event.matches, currentColorScheme);
    };

    const cleanup = () => {
        mediaQueryList.removeEventListener("change", changeListener);
    };

    const mediaQueryList = createColorSchemeTarget(colorScheme);

    mediaQueryList.addEventListener("change", changeListener, {
        signal,
    });

    // Trigger the effect immediately.
    effect(
        mediaQueryList.matches,
        mediaQueryList.matches ? colorScheme : ColorSchemeInversion[colorScheme],
    );

    // Return the cleanup function.
    return cleanup;
}
