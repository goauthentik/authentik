import { DefaultClient, AKResponse, QueryArguments } from "./Client";
import { Group } from "./Groups";
import { Policy } from "./Policies";
import { User } from "./Users";

export class PolicyBinding {
    pk: string;
    policy: string;
    policy_obj?: Policy;
    group?: Group;
    user?: User;
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

    static list(filter?: QueryArguments): Promise<AKResponse<PolicyBinding>> {
        return DefaultClient.fetch<AKResponse<PolicyBinding>>(["policies", "bindings"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/policies/bindings/${rest}`;
    }
}
