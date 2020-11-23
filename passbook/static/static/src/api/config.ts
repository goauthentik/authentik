export interface Config {
    branding_logo: string;
    branding_title: string;
}

export function getConfig(): Promise<Config> {
    return fetch("/api/v2beta/root/config/")
        .then((r) => r.json())
        .then((r) => <Config>r);
}
