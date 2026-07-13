import { aki } from "#common/api/client";

import { PropertymappingsApi, ScopeMapping } from "@goauthentik/api";

const mappingToSelect = (s: ScopeMapping) => [s.pk, s.name, s.name, s];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await aki(PropertymappingsApi).propertymappingsProviderScopeList({
        ordering: "scope_name",
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results.map(mappingToSelect),
    };
}

export function propertyMappingsSelector(instanceMappings?: string[]) {
    if (!instanceMappings) {
        return async () => [];
    }

    return async () => {
        const pm = aki(PropertymappingsApi);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsProviderScopeRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
