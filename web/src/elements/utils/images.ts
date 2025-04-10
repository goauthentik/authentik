import { resolveColorScheme } from "@goauthentik/common/color-scheme";
import { findThemedRootElement } from "@goauthentik/elements/utils/theme";

/**
 * Given an image path, replace the %theme% placeholder with the current color scheme.
 */
export function themeImage(rawPath: string) {
    const colorScheme = resolveColorScheme(findThemedRootElement()?.colorScheme);

    return rawPath.replaceAll("%(theme)s", colorScheme);
}
