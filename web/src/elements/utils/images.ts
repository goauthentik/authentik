import { ResolvedUITheme } from "#common/theme";

export function themeImage(rawPath: string, theme: ResolvedUITheme) {
    return rawPath.replaceAll("%(theme)s", theme);
}
