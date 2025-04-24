import { QUERY_MEDIA_COLOR_LIGHT, rootInterface } from "@goauthentik/elements/Base";

import { UiThemeEnum } from "@goauthentik/api";

export function themeImage(rawPath: string) {
    let enabledTheme = rootInterface()?.activeTheme;
    if (!enabledTheme || enabledTheme === UiThemeEnum.Automatic) {
        enabledTheme = window.matchMedia(QUERY_MEDIA_COLOR_LIGHT).matches
            ? UiThemeEnum.Light
            : UiThemeEnum.Dark;
    }
    return rawPath.replaceAll("%(theme)s", enabledTheme);
}
