import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { msg, str } from "@lit/localize";

import { PoliciesApi, Policy, Prompt, StagesApi } from "@goauthentik/api";

export async function promptFieldsProvider(page = 1, search = "") {
    const prompts = await new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList({
        ordering: "field_name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: prompts.pagination,
        options: prompts.results.map((prompt) => [
            prompt.pk,
            msg(str`${prompt.name} ("${prompt.fieldKey}", of type ${prompt.type})`),
        ]),
    };
}

export function promptFieldsSelector(instanceFields: string[] | undefined) {
    if (!instanceFields) {
        return async (options: DualSelectPair<Prompt>) =>
            options.filter(([_0, _1, _2, prompt]: DualSelectPair<Prompt>) => prompt !== undefined);
    }
    return async () => {
        const stages = new StagesApi(DEFAULT_CONFIG);
        const prompts = await Promise.allSettled(
            instanceFields.map((instanceId) => stages.stagesPromptPromptsRetrieve({ promptUuid: instanceId }))
        );
        return prompts
            .filter((p) => p.status === "fulfilled")
            .map((p) => p.value)
            .map((p) => [p.pk, msg(str`${p.name} ("${p.fieldKey}", of type ${p.type})`), p.name, p]);
    };
}

export async function policiesProvider(page = 1, search = "") {
    const policies = await new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: policies.pagination,
        options: policies.results.map((policy) => [policy.pk, `${policy.name} (${policy.verboseName})`]),
    };
}

export function policiesSelector(instancePolicies: string[] | undefined) {
    if (!instancePolicies) {
        return async (options: DualSelectPair<Policy>) =>
            options.filter(([_0, _1, _2, policy]: DualSelectPair<Policy>) => policy !== undefined);
    }

    return async () => {
        const policy = new PoliciesApi(DEFAULT_CONFIG);
        const policies = await Promise.allSettled(
            instancePolicies.map((instanceId) => policy.policiesAllRetrieve({ policyUuid: instanceId }))
        );
        return policies
            .filter((p) => p.status === "fulfilled")
            .map((p) => p.value)
            .map((p) => [p.pk, `${p.name} (${p.verbose_name})`, p.name, p]);
    };
}
