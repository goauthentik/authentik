import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { PoliciesApi, Policy, Prompt, StagesApi } from "@goauthentik/api";

/**
 * Resolve an ordered list of prompt UUIDs to their full {@link Prompt} objects, preserving
 * the given order (which encodes the per-stage field order).
 */
export async function resolvePrompts(pks: string[]): Promise<Prompt[]> {
    if (pks.length === 0) {
        return [];
    }
    const { results } = await aki(StagesApi).stagesPromptPromptsList({
        pks,
        // Fetch them all in one page; the caller passes one stage's worth of fields.
        pageSize: pks.length,
    });
    // The `pks` filter does not preserve order, so sort back into the requested (per-stage) order.
    const orderByPk = new Map(pks.map((pk, index) => [pk, index]));
    return results
        .filter((prompt) => orderByPk.has(prompt.pk))
        .sort((a, b) => (orderByPk.get(a.pk) ?? 0) - (orderByPk.get(b.pk) ?? 0));
}

const policyToSelect = (p: Policy) => [p.pk, `${p.name} (${p.verboseName})`, p.name, p];

export async function policiesProvider(page = 1, search = "") {
    const policies = await aki(PoliciesApi).policiesAllList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: policies.pagination,
        options: policies.results.map(policyToSelect),
    };
}

export function policiesSelector(instancePolicies: string[] | undefined) {
    if (!instancePolicies) {
        return async (options: DualSelectPair<Policy>[]) =>
            options.filter(([_0, _1, _2, policy]: DualSelectPair<Policy>) => policy !== undefined);
    }

    return async () => {
        const policy = aki(PoliciesApi);
        const policies = await Promise.allSettled(
            instancePolicies.map((instanceId) =>
                policy.policiesAllRetrieve({ policyUuid: instanceId }),
            ),
        );
        return policies
            .filter((p) => p.status === "fulfilled")
            .map((p) => p.value)
            .map(policyToSelect);
    };
}
