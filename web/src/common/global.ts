import {
    Config,
    ConfigFromJSON,
    CurrentBrand,
    CurrentBrandFromJSON,
    ErrorReportingConfigFromJSON,
    UiThemeEnum,
} from "@goauthentik/api";

export interface GlobalAuthentik {
    _converted?: boolean;
    locale?: string;
    flow?: {
        layout: string;
    };
    config: Config;
    brand: CurrentBrand;
    versionFamily: string;
    versionSubdomain: string;
    build: string;
}

export interface AuthentikWindow {
    authentik: GlobalAuthentik;
}

export function globalAK(): GlobalAuthentik {
    const ak = (window as unknown as AuthentikWindow).authentik;
    if (ak && !ak._converted) {
        ak._converted = true;
        ak.brand = CurrentBrandFromJSON(ak.brand);
        ak.config = ConfigFromJSON(ak.config);
    }
    if (!ak) {
        return {
            config: ConfigFromJSON({
                capabilities: [],
                error_reporting: ErrorReportingConfigFromJSON({}),
            }),
            brand: CurrentBrandFromJSON({
                matched_domain: window.location.host,
                ui_footer_links: [],
                ui_theme: window.authentik_sdk?.forceTheme ?? UiThemeEnum.Automatic,
            }),
            versionFamily: "",
            versionSubdomain: "",
            build: "",
        };
    }
    return ak;
}

export function isEmbedded() {
    return !!window.authentik_sdk;
}

export function docLink(path: string): string {
    const ak = globalAK();
    // Default case or beta build which should always point to latest
    if (!ak || ak.build !== "") {
        return `https://goauthentik.io${path}`;
    }
    return `https://${ak.versionSubdomain}.goauthentik.io${path}`;
}
