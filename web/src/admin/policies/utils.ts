import { msg } from "@lit/localize";

export enum PolicyBindingCheckTarget {
    policy = "policy",
    group = "group",
    user = "user",
}

export function PolicyBindingCheckTargetToLabel(ct: PolicyBindingCheckTarget): string {
    switch (ct) {
        case PolicyBindingCheckTarget.group:
            return msg("Group");
        case PolicyBindingCheckTarget.user:
            return msg("User");
        case PolicyBindingCheckTarget.policy:
            return msg("Policy");
    }
}
