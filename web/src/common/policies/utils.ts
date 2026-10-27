import { RadioOption } from "#elements/forms/Radio";
import { toAdminInterface } from "#elements/router/core/interfaces";

import { PolicyBinding } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderDryRunHelp() {
    return msg(
        html`Evaluate this binding without including its result or messages in the final decision.
            Results are recorded in the <a href=${toAdminInterface("events/log")}>Event Log</a>.
            Expression policies can still make network requests, create events, or modify data.`,
        { id: "policies.bindings.dry-run.description" },
    );
}

export enum PolicyBindingCheckTarget {
    Policy = "policy",
    Group = "group",
    User = "user",
}

export const PolicyBindingCheckTargetToLabel = (ct: PolicyBindingCheckTarget) =>
    match(ct)
        .with(PolicyBindingCheckTarget.Group, () => msg("Group"))
        .with(PolicyBindingCheckTarget.User, () => msg("User"))
        .with(PolicyBindingCheckTarget.Policy, () => msg("Policy"))
        .exhaustive();

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
