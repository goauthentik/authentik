import { RadioOption } from "#elements/forms/Radio";

import { PolicyBinding } from "@goauthentik/api";

import { msg } from "@lit/localize";

export enum PolicyBindingCheckTarget {
    Policy = "policy",
    Group = "group",
    User = "user",
}

export function PolicyBindingCheckTargetToLabel(ct: PolicyBindingCheckTarget): string {
    switch (ct) {
        case PolicyBindingCheckTarget.Group:
            return msg("Group");
        case PolicyBindingCheckTarget.User:
            return msg("User");
        case PolicyBindingCheckTarget.Policy:
            return msg("Policy");
    }
}

export const PolicyObjectKeys = {
    [PolicyBindingCheckTarget.Policy]: "policyObj",
    [PolicyBindingCheckTarget.Group]: "groupObj",
    [PolicyBindingCheckTarget.User]: "userObj",
} as const satisfies Record<PolicyBindingCheckTarget, keyof PolicyBinding>;

export function createPassFailOptions(): RadioOption<boolean>[] {
    return [
        {
            label: msg("Pass"),
            value: true,
        },
        {
            label: msg("Don't Pass"),
            value: false,
            default: true,
        },
    ];
}
