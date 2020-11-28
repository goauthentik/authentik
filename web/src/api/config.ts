import { DefaultClient } from "./client";

export class Config {
    branding_logo?: string;
    branding_title?: string;

    static get(): Promise<Config> {
        return DefaultClient.fetch<Config>("root", "config");
    }
}
