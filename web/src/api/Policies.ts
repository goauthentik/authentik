import { DefaultClient, BaseInheritanceModel, AKResponse, QueryArguments } from "./Client";

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

    static list(filter?: QueryArguments): Promise<AKResponse<Policy>> {
        return DefaultClient.fetch<AKResponse<Policy>>(["policies", "all"], filter);
    }

    static cached(): Promise<number> {
        return DefaultClient.fetch<{ count: number }>(["policies", "all", "cached"]).then(r => {
            return r.count;
        });
    }
}
