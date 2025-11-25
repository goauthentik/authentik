import { ResolvedUITheme } from "#common/theme";

export function themeImage(rawPath: string, theme: ResolvedUITheme) {
    return rawPath.replaceAll("%(theme)s", theme);
}

export function isDefaultAvatar(path?: string | null): boolean {
    return !!path?.endsWith("user_default.png");
}
