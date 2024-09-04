import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { PropertymappingsApi, ScopeMapping } from "@goauthentik/api";

export const defaultScopes = [
    "goauthentik.io/providers/oauth2/scope-openid",
    "goauthentik.io/providers/oauth2/scope-email",
    "goauthentik.io/providers/oauth2/scope-profile",
];

export async function oauth2PropertyMappingsProvider(page = 1, search = "") {
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

export function makeOAuth2PropertyMappingsSelector(instanceMappings: string[] | undefined) {
    const localMappings = instanceMappings ? new Set(instanceMappings) : undefined;
    return localMappings
        ? ([pk, _]: DualSelectPair) => localMappings.has(pk)
        : ([_0, _1, _2, scope]: DualSelectPair<ScopeMapping>) =>
              scope?.managed && defaultScopes.includes(scope?.managed);
}
