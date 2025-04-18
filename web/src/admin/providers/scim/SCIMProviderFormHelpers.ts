import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { CoreApi, Group, PropertymappingsApi, SCIMMapping } from "@goauthentik/api";

const mappingToSelect = (m: SCIMMapping) => [m.pk, m.name, m.name, m];
const groupToSelect = (g: Group) => [g.pk, g.name, g.name, g];

export async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsProviderScimList({
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
    defaultSelected: string,
) {
    if (!instanceMappings) {
        return async (mappings: DualSelectPair<SCIMMapping>[]) =>
            mappings.filter(
                ([_0, _1, _2, mapping]: DualSelectPair<SCIMMapping>) =>
                    mapping?.managed === defaultSelected,
            );
    }

    return async () => {
        const pm = new PropertymappingsApi(DEFAULT_CONFIG);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.propertymappingsProviderScimRetrieve({ pmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(mappingToSelect);
    };
}

export async function groupsProvider(page = 1, search = "") {
    const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList({
        ordering: "name",
        includeUsers: false,
        pageSize: 20,
        search: search.trim(),
        page,
    });
    return {
        pagination: groups.pagination,
        options: groups.results.map(groupToSelect),
    };
}

export function groupsSelector(
    instanceGroups: string[] | undefined,
    defaultSelected: string | null = null,
) {
    // If we have no instance groups (new provider), return empty selection
    // if (!instanceGroups || instanceGroups.length === 0) {
    if (!instanceGroups) {
        return async (groups: DualSelectPair<Group>[]) =>
            groups.filter(
                ([_0, _1, _2, group]: DualSelectPair<Group>) => group?.name === defaultSelected,
            );
    }

    // For existing providers, load the selected groups
    return async () => {
        const groups = await Promise.allSettled(
            instanceGroups.map((groupId) =>
                new CoreApi(DEFAULT_CONFIG).coreGroupsRetrieve({ groupUuid: groupId }),
            ),
        );

        return groups
            .filter((s) => s.status === "fulfilled")
            .map((s) => (s as PromiseFulfilledResult<Group>).value)
            .map(groupToSelect);
    };
}
