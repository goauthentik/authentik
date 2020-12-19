import { DefaultClient, PBResponse, QueryArguments } from "./Client";

export class Provider {
    pk: number;
    name: string;
    authorization_flow: string;

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<Provider> {
        return DefaultClient.fetch<Provider>(["providers", "all", slug]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Provider>> {
        return DefaultClient.fetch<PBResponse<Provider>>(["providers", "all"], filter);
    }
}
