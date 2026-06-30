import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { PropertymappingsApi, SAMLPropertyMapping } from "@goauthentik/api";

const mappingToSelect = (m: SAMLPropertyMapping) => [m.pk, m.name, m.name, m];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await aki(PropertymappingsApi).propertymappingsProviderSamlList({
        ordering: "saml_name",
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
        return async (mappings: DualSelectPair<SAMLPropertyMapping>[]) =>
            mappings.filter(([_0, _1, _2, mapping]: DualSelectPair<SAMLPropertyMapping>) =>
                mapping?.managed?.startsWith("goauthentik.io/providers/saml"),
            );
    }

    return async () => {
        const pm = aki(PropertymappingsApi);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsProviderSamlRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
