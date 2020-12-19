import { DefaultClient, PBResponse, QueryArguments } from "./Client";

export class Application {
    pk: string;
    name: string;
    slug: string;
    provider: number;

    launch_url: string;
    meta_launch_url: string;
    meta_icon: string;
    meta_description: string;
    meta_publisher: string;
    policies: string[];

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<Application> {
        return DefaultClient.fetch<Application>(["core", "applications", slug]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Application>> {
        return DefaultClient.fetch<PBResponse<Application>>(["core", "applications"], filter);
    }
}
