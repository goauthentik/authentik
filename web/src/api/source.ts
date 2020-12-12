import { DefaultClient, PBResponse, QueryArguments } from "./client";

export class Source {
    pk: string;
    name: string;
    slug: string;
    enabled: boolean;
    authentication_flow: string;
    enrollment_flow: string;

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<Source> {
        return DefaultClient.fetch<Source>(["sources", "all", slug]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Source>> {
        return DefaultClient.fetch<PBResponse<Source>>(["sources", "all"], filter);
    }
}
