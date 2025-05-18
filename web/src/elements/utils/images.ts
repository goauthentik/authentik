import { resolveUITheme } from "@goauthentik/common/theme";
import { rootInterface } from "@goauthentik/elements/Base";

export function themeImage(rawPath: string) {
    const enabledTheme = rootInterface()?.activeTheme || resolveUITheme();

    return rawPath.replaceAll("%(theme)s", enabledTheme);
}
