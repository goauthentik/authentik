export interface Policy {
    pk: string;
    name: string;
    [key: string]: unknown;
}

export interface PolicyBinding {
    pk: string;
    policy: string,
    policy_obj: Policy;
    target: string;
    enabled: boolean;
    order: number;
    timeout: number;
}
