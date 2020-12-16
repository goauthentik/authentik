import { DefaultClient, PBResponse, QueryArguments } from "./client";

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

export class PolicyBinding {
    pk: string;
    policy: string;
    policy_obj: Policy;
    target: string;
    enabled: boolean;
    order: number;
    timeout: number;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<PolicyBinding> {
        return DefaultClient.fetch<PolicyBinding>(["policies", "bindings", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<PolicyBinding>> {
        return DefaultClient.fetch<PBResponse<PolicyBinding>>(["policies", "bindings"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/policies/bindings/${rest}`;
    }
}
