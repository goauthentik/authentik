import { VERSION } from "../../../constants";

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
}

export const DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Plex-Product": "authentik",
    "X-Plex-Version": VERSION,
    "X-Plex-Device-Vendor": "BeryJu.org",
};

export class PlexAPIClient {

    token: string;

    constructor(token: string) {
        this.token = token;
    }

    static async getPin(clientIdentifier: string): Promise<{ authUrl: string, pin: PlexPinResponse }> {
        const headers = { ...DEFAULT_HEADERS, ...{
            "X-Plex-Client-Identifier": clientIdentifier
        }};
        const pinResponse = await fetch("https://plex.tv/api/v2/pins.json?strong=true", {
            method: "POST",
            headers: headers
        });
        const pin: PlexPinResponse = await pinResponse.json();
        return {
            authUrl: `https://app.plex.tv/auth#!?clientID=${encodeURIComponent(clientIdentifier)}&code=${pin.code}`,
            pin: pin
        };
    }

    static async pinStatus(id: number): Promise<string> {
        const pinResponse = await fetch(`https://plex.tv/api/v2/pins/${id}`, {
            headers: DEFAULT_HEADERS
        });
        const pin: PlexPinResponse = await pinResponse.json();
        return pin.authToken || "";
    }

    async getServers(): Promise<PlexResource[]> {
        const resourcesResponse = await fetch(`https://plex.tv/api/v2/resources?X-Plex-Token=${this.token}&X-Plex-Client-Identifier=authentik`, {
            headers: DEFAULT_HEADERS
        });
        const resources: PlexResource[] = await resourcesResponse.json();
        return resources.filter(r => {
            return r.provides === "server";
        });
    }

}
