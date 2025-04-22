import { resolveColorScheme } from "@goauthentik/common/color-scheme";

/**
 * Given an image path, replace the %theme% placeholder with the current color scheme.
 */
export function themeImage(rawPath: string) {
    const colorScheme = resolveColorScheme();

    return rawPath.replaceAll("%(theme)s", colorScheme);
}
