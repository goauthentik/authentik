import { Config, ConfigFromJSON, CurrentTenant, CurrentTenantFromJSON } from "@goauthentik/api";

export interface GlobalAuthentik {
    _converted?: boolean;
    locale?: string;
    flow?: {
        layout: string;
    };
    config: Config;
    tenant: CurrentTenant;
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
        ak.tenant = CurrentTenantFromJSON(ak.tenant);
        ak.config = ConfigFromJSON(ak.config);
    }
    if (!ak) {
        return {
            config: ConfigFromJSON({
                capabilities: [],
            }),
            tenant: CurrentTenantFromJSON({
                ui_footer_links: [],
            }),
            versionFamily: "",
            versionSubdomain: "",
            build: "",
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
