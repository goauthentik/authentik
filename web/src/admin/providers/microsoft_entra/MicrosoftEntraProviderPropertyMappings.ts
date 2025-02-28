import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

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
    const localMappings = instanceMappings ? new Set(instanceMappings) : undefined;
    return localMappings
        ? ([pk, _]: DualSelectPair) => localMappings.has(pk)
        : ([_0, _1, _2, scope]: DualSelectPair<ScopeMapping>) =>
              scope?.managed === defaultSelection;
}
