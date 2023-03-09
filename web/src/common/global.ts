import { Config, CurrentTenant } from "@goauthentik/api";

export interface GlobalAuthentik {
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
    authentik?: GlobalAuthentik;
}

export function globalAK(): GlobalAuthentik | undefined {
    return (window as unknown as AuthentikWindow).authentik;
}

export function docLink(path: string): string {
    const ak = globalAK();
    // Default case or beta build which should always point to latest
    if (!ak || ak.build !== "") {
        return `https://goauthentik.io${path}`;
    }
    return `https://${ak.versionSubdomain}.goauthentik.io${path}`;
}
