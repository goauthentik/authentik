import { Config, CurrentTenant } from "@goauthentik/api";

export interface GlobalAuthentik {
    locale?: string;
    flow?: {
        layout: string;
    };
    config: Config;
    tenant: CurrentTenant;
}

export interface AuthentikWindow {
    authentik?: GlobalAuthentik;
}

export function globalAK(): GlobalAuthentik | undefined {
    return (window as unknown as AuthentikWindow).authentik;
}
