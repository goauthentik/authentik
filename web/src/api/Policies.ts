import { DefaultClient, PBResponse, QueryArguments } from "./Client";

export class Policy {
    pk: string;
    name: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Policy> {
        return DefaultClient.fetch<Policy>(["policies", "all", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Policy>> {
        return DefaultClient.fetch<PBResponse<Policy>>(["policies", "all"], filter);
    }

    static cached(): Promise<number> {
        return DefaultClient.fetch<PBResponse<Policy>>(["policies", "cached"]).then(r => {
            return r.pagination.count;
        });
    }
}
