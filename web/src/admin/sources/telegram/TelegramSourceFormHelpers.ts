import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { PropertymappingsApi, TelegramSourcePropertyMapping } from "@goauthentik/api";

const mappingToSelect = (m: TelegramSourcePropertyMapping) => [m.pk, m.name, m.name, m];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await aki(PropertymappingsApi).propertymappingsSourceTelegramList({
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

export function propertyMappingsSelector(instanceMappings?: string[]) {
    if (!instanceMappings) {
        return async (mappings: DualSelectPair<TelegramSourcePropertyMapping>[]) =>
            mappings.filter(
                ([_0, _1, _2, _3]: DualSelectPair<TelegramSourcePropertyMapping>) => false,
            );
    }

    return async () => {
        const pm = aki(PropertymappingsApi);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsSourceTelegramRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
