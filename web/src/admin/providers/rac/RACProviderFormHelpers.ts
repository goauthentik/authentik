import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { PropertymappingsApi, RACPropertyMapping } from "@goauthentik/api";

const mappingToSelect = (m: RACPropertyMapping) => [m.pk, m.name, m.name, m];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await aki(PropertymappingsApi).propertymappingsProviderRacList({
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
        return async (_mappings: DualSelectPair<RACPropertyMapping>[]) => [];
    }

    return async () => {
        const pm = aki(PropertymappingsApi);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsProviderRacRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
