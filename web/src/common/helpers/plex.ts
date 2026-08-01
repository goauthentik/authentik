import { SentryIgnoredError } from "#common/sentry/index";

export interface PlexPinResponse {
    // Only has the fields we care about
    authToken?: string;
    code: string;
    id: number;
}

export interface PlexResource {
    name: string;
    provides: string;
    clientIdentifier: string;
    owned: boolean;
}

export const DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Plex-Product": "authentik",
    "X-Plex-Version": import.meta.env.AK_VERSION,
    "X-Plex-Device-Vendor": "goauthentik.io",
};

export async function popupCenterScreen(
    url: string,
    title: string,
    w: number,
    h: number,
): Promise<Window | null> {
    const top = (screen.height - h) / 4,
        left = (screen.width - w) / 2;
    // window.open must run synchronously in the caller's task: opened from
    // inside a setTimeout it has no transient user activation and is popup
    // blocked by current browsers.
    return window.open(url, title, `scrollbars=yes,width=${w},height=${h},top=${top},left=${left}`);
}

export class PlexAPIClient {
    token: string;

    constructor(token: string) {
        this.token = token;
    }

    // The #? form is the one app.plex.tv documents; forwardUrl is only known to
    // work with it, not with the older #!? form.
    static authUrl(clientIdentifier: string, code: string, forwardUrl?: string): string {
        let url = `https://app.plex.tv/auth#?clientID=${encodeURIComponent(clientIdentifier)}&code=${encodeURIComponent(code)}`;
        if (forwardUrl) {
            url += `&forwardUrl=${encodeURIComponent(forwardUrl)}&context[device][product]=authentik`;
        }
        return url;
    }

    static async getPin(
        clientIdentifier: string,
    ): Promise<{ authUrl: string; pin: PlexPinResponse }> {
        const headers = {
            ...DEFAULT_HEADERS,
            "X-Plex-Client-Identifier": clientIdentifier,
        };
        const pinResponse = await fetch("https://plex.tv/api/v2/pins.json?strong=true", {
            method: "POST",
            headers: headers,
        });
        const pin: PlexPinResponse = await pinResponse.json();
        return {
            authUrl: PlexAPIClient.authUrl(clientIdentifier, pin.code),
            pin: pin,
        };
    }

    static async pinStatus(clientIdentifier: string, id: number): Promise<string | undefined> {
        const headers = {
            ...DEFAULT_HEADERS,
            "X-Plex-Client-Identifier": clientIdentifier,
        };
        const pinResponse = await fetch(`https://plex.tv/api/v2/pins/${id}`, {
            headers: headers,
        });
        if (pinResponse.status > 200) {
            throw new SentryIgnoredError("Invalid response code");
        }
        const pin: PlexPinResponse = await pinResponse.json();
        console.debug("authentik/plex: polling Pin");
        return pin.authToken;
    }

    static async pinPoll(clientIdentifier: string, id: number, timeout?: number): Promise<string> {
        const deadline = timeout ? Date.now() + timeout : undefined;
        const executePoll = async (
            resolve: (authToken: string) => void,
            reject: (e: Error) => void,
        ) => {
            try {
                const response = await PlexAPIClient.pinStatus(clientIdentifier, id);

                if (response) {
                    resolve(response);
                } else if (deadline !== undefined && Date.now() >= deadline) {
                    reject(
                        new SentryIgnoredError("Plex pin was not authorized before the timeout"),
                    );
                } else {
                    setTimeout(executePoll, 500, resolve, reject);
                }
            } catch (e) {
                reject(e as Error);
            }
        };

        return new Promise(executePoll);
    }

    async getServers(): Promise<PlexResource[]> {
        const resourcesResponse = await fetch(
            `https://plex.tv/api/v2/resources?X-Plex-Token=${this.token}&X-Plex-Client-Identifier=authentik`,
            {
                headers: DEFAULT_HEADERS,
            },
        );
        const resources: PlexResource[] = await resourcesResponse.json();
        return resources.filter((r) => {
            return r.provides.toLowerCase().includes("server") && r.owned;
        });
    }
}
