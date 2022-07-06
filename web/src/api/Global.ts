export interface GlobalAuthentik {
    locale?: string;
    flow?: {
        layout: string;
    };
}

export interface AuthentikWindow {
    authentik?: GlobalAuthentik;
}

export function globalAK(): GlobalAuthentik | undefined {
    return (window as unknown as AuthentikWindow).authentik;
}
