import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { PropertymappingsApi } from "@goauthentik/api";

export async function proxyPropertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsScopeList({
        ordering: "scope_name",
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results
            .filter((scope) => !(scope?.managed ?? "").startsWith("goauthentik.io/providers"))
            .map((scope) => [scope.pk, scope.name]),
    };
}

export function makeProxyPropertyMappingsSelector(mappings?: string[]) {
    const localMappings = new Set(mappings ?? []);
    return ([pk, _]: DualSelectPair) => localMappings.has(pk);
}
