import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { MicrosoftEntraProviderMapping, PropertymappingsApi } from "@goauthentik/api";

const mappingToSelect = (m: MicrosoftEntraProviderMapping) => [m.pk, m.name, m.name, m];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await aki(
        PropertymappingsApi,
    ).propertymappingsProviderMicrosoftEntraList({
        ordering: "managed",
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results.map(mappingToSelect),
    };
}

export function propertyMappingsSelector(
    instanceMappings: string[] | undefined,
    defaultSelection: string,
) {
    if (!instanceMappings) {
        return async (mappings: DualSelectPair<MicrosoftEntraProviderMapping>[]) =>
            mappings.filter(
                ([_0, _1, _2, mapping]: DualSelectPair<MicrosoftEntraProviderMapping>) =>
                    mapping?.managed === defaultSelection,
            );
    }

    return async () => {
        const pm = aki(PropertymappingsApi);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsProviderMicrosoftEntraRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
