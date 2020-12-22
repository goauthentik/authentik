import { DefaultClient, PBResponse, QueryArguments } from "./Client";
import { Provider } from "./Providers";

export class Application {
    pk: string;
    name: string;
    slug: string;
    provider: Provider;

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

    static adminUrl(rest: string): string {
        return `/administration/applications/${rest}`;
    }
}
