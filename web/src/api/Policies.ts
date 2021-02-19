import { DefaultClient, BaseInheritanceModel, AKResponse, QueryArguments } from "./Client";
import { TypeCreate } from "./Providers";

export class Policy implements BaseInheritanceModel {
    pk: string;
    name: string;
    execution_logging: boolean;
    object_type: string;
    verbose_name: string;
    verbose_name_plural: string;
    bound_to: number;

    constructor() {
        throw Error();
    }

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

    static getTypes(): Promise<TypeCreate[]> {
        return DefaultClient.fetch<TypeCreate[]>(["policies", "all", "types"]);
    }

    static adminUrl(rest: string): string {
        return `/administration/policies/${rest}`;
    }
}
