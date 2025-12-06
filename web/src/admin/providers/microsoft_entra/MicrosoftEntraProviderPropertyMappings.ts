import { DEFAULT_CONFIG } from "#common/api/config";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { PropertymappingsApi, ScopeMapping } from "@goauthentik/api";

export async function microsoftEntraPropertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsProviderMicrosoftEntraList({
        ordering: "managed",
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results.map((scope) => [scope.pk, scope.name, scope.name, scope]),
    };
}

export function makeMicrosoftEntraPropertyMappingsSelector(
    instanceMappings: string[] | undefined,
    defaultSelection: string,
) {
    const localMappings = instanceMappings ? new Set<string | number>(instanceMappings) : undefined;
    return localMappings
        ? ([pk, _]: DualSelectPair) => localMappings.has(pk)
        : ([_0, _1, _2, scope]: DualSelectPair<ScopeMapping>) =>
              scope?.managed === defaultSelection;
}
