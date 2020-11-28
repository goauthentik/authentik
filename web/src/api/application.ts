import { DefaultClient } from "./client";

export class Application {
    pk?: string;
    name?: string;
    slug?: string;
    provider?: number;

    meta_launch_url?: string;
    meta_icon?: string;
    meta_description?: string;
    meta_publisher?: string;
    policies?: string[];

    static get(slug: string): Promise<Application> {
        return DefaultClient.fetch<Application>("core", "applications", slug);
    }
}
