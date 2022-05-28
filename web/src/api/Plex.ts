import { SentryIgnoredError } from "../common/errors";
import { VERSION } from "../constants";

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
    "X-Plex-Version": VERSION,
    "X-Plex-Device-Vendor": "goauthentik.io",
};

export function popupCenterScreen(url: string, title: string, w: number, h: number): Window | null {
    const top = (screen.height - h) / 4,
        left = (screen.width - w) / 2;
    const popup = window.open(
        url,
        title,
        `scrollbars=yes,width=${w},height=${h},top=${top},left=${left}`,
    );
    return popup;
}

export class PlexAPIClient {
    token: string;

    constructor(token: string) {
        this.token = token;
    }

    static async getPin(
        clientIdentifier: string,
    ): Promise<{ authUrl: string; pin: PlexPinResponse }> {
        const headers = {
            ...DEFAULT_HEADERS,
            ...{
                "X-Plex-Client-Identifier": clientIdentifier,
            },
        };
        const pinResponse = await fetch("https://plex.tv/api/v2/pins.json?strong=true", {
            method: "POST",
            headers: headers,
        });
        const pin: PlexPinResponse = await pinResponse.json();
        return {
            authUrl: `https://app.plex.tv/auth#!?clientID=${encodeURIComponent(
                clientIdentifier,
            )}&code=${pin.code}`,
            pin: pin,
        };
    }

    static async pinStatus(clientIdentifier: string, id: number): Promise<string | undefined> {
        const headers = {
            ...DEFAULT_HEADERS,
            ...{
                "X-Plex-Client-Identifier": clientIdentifier,
            },
        };
        const pinResponse = await fetch(`https://plex.tv/api/v2/pins/${id}`, {
            headers: headers,
        });
        if (pinResponse.status > 200) {
            throw new SentryIgnoredError("Invalid response code")
        }
        const pin: PlexPinResponse = await pinResponse.json();
        console.debug(`authentik/plex: polling Pin`);
        return pin.authToken;
    }

    static async pinPoll(clientIdentifier: string, id: number): Promise<string> {
        const executePoll = async (
            resolve: (authToken: string) => void,
            reject: (e: Error) => void,
        ) => {
            try {
                const response = await PlexAPIClient.pinStatus(clientIdentifier, id);

                if (response) {
                    resolve(response);
                } else {
                    setTimeout(executePoll, 500, resolve, reject);
                }
            } catch (e) {
                reject(e);
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
