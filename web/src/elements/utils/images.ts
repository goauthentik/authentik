import { resolveUITheme, rootInterface } from "#common/theme";
import type { AKElement } from "#elements/Base";

export function themeImage(rawPath: string) {
    const enabledTheme = rootInterface<AKElement>()?.activeTheme || resolveUITheme();

    return rawPath.replaceAll("%(theme)s", enabledTheme);
}
