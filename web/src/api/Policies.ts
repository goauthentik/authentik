import { DefaultClient, BaseInheritanceModel, PBResponse, QueryArguments } from "./Client";

export class Policy implements BaseInheritanceModel {
    pk: string;
    name: string;

    constructor() {
        throw Error();
    }
    object_type: string;
    verbose_name: string;
    verbose_name_plural: string;

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
