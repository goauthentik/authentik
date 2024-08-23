import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { PropertymappingsApi, ScopeMapping } from "@goauthentik/api";

export async function proxyPropertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsProviderScopeList({
        ordering: "scope_name",
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results.map((scope) => [scope.pk, scope.name, scope.name, scope]),
    };
}

export function makeProxyPropertyMappingsSelector(mappings?: string[]) {
    const localMappings = mappings ? new Set(mappings) : undefined;
    return localMappings
        ? ([pk, _]: DualSelectPair) => localMappings.has(pk)
        : ([_0, _1, _2, scope]: DualSelectPair<ScopeMapping>) =>
              !(scope?.managed ?? "").startsWith("goauthentik.io/providers");
}
