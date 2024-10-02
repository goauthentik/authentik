import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { PropertymappingsApi } from "@goauthentik/api";

export async function racPropertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsProviderRacList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results.map((mapping) => [mapping.pk, mapping.name]),
    };
}

export function makeRACPropertyMappingsSelector(instanceMappings?: string[]) {
    const localMappings = new Set(instanceMappings ?? []);
    return ([pk, _]: DualSelectPair) => localMappings.has(pk);
}
