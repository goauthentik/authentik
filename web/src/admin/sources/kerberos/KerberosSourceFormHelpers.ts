import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { KerberosSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

const mappingToSelect = (m: KerberosSourcePropertyMapping) => [m.pk, m.name, m.name, m];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsSourceKerberosList({
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

export function propertyMappingsSelector(object: string, instanceMappings?: string[]) {
    if (!instanceMappings) {
        return async (mappings: DualSelectPair<KerberosSourcePropertyMapping>[]) =>
            mappings.filter(
                ([_0, _1, _2, mapping]: DualSelectPair<KerberosSourcePropertyMapping>) =>
                    object == "user" &&
                    mapping?.managed?.startsWith("goauthentik.io/sources/kerberos/user/default/"),
            );
    }

    return async () => {
        const pm = new PropertymappingsApi(DEFAULT_CONFIG);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsSourceKerberosRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}
