import { DefaultClient, PBResponse, QueryArguments } from "./client";

export interface Policy {
    pk: string;
    name: string;
    [key: string]: unknown;
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
