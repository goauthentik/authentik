import { Config, ConfigFromJSON, CurrentBrand, CurrentBrandFromJSON } from "@goauthentik/api";

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
    api: {
        base: string;
        relBase: string;
    };
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
    const apiBase = new URL(process.env.AK_API_BASE_PATH || window.location.origin);
    if (!ak) {
        return {
            config: ConfigFromJSON({
                capabilities: [],
            }),
            brand: CurrentBrandFromJSON({
                ui_footer_links: [],
            }),
            versionFamily: "",
            versionSubdomain: "",
            build: "",
            api: {
                base: apiBase.toString(),
                relBase: apiBase.pathname,
            },
        };
    }
    return ak;
}

export function docLink(path: string): string {
    const ak = globalAK();
    // Default case or beta build which should always point to latest
    if (!ak || ak.build !== "") {
        return `https://goauthentik.io${path}`;
    }
    return `https://${ak.versionSubdomain}.goauthentik.io${path}`;
}
