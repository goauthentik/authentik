import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { PropertymappingsApi, RadiusProviderPropertyMapping } from "@goauthentik/api";

const mappingToSelect = (m: RadiusProviderPropertyMapping) => [m.pk, m.name, m.name, m];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsProviderRadiusList({
        ordering: "name",
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
        return async (_mappings: DualSelectPair<RadiusProviderPropertyMapping>[]) => [];
    }

    return async () => {
        const pm = new PropertymappingsApi(DEFAULT_CONFIG);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsProviderRadiusRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
