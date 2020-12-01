import { DefaultClient } from "./client";

export class AdminOverview {
    version: string;
    version_latest: string;
    worker_count: number;
    providers_without_application: number;
    policies_without_binding: number;
    cached_policies: number;
    cached_flows: number;

    constructor() {
        throw Error();
    }

    static get(): Promise<AdminOverview> {
        return DefaultClient.fetch<AdminOverview>(["admin", "overview"]);
    }

}
