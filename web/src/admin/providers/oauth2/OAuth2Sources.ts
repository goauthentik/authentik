import { DEFAULT_CONFIG } from "#common/api/config";

import { DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";

import { OAuthSource, SourcesApi } from "@goauthentik/api";

const sourceToSelect = (source: OAuthSource): DualSelectPair<OAuthSource> => [
    source.pk,
    `${source.name} (${source.slug})`,
    source.name,
    source,
];

export async function oauth2SourcesProvider(page = 1, search = "") {
    const oauthSources = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthList({
        ordering: "name",
        hasJwks: true,
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: oauthSources.pagination,
        options: oauthSources.results.map(sourceToSelect),
    };
}

export function oauth2SourcesSelector(instanceMappings?: string[]): DualSelectPairSource {
    if (!instanceMappings) {
        return async () => [];
    }

    const fetchAvailableOauth2Sources: DualSelectPairSource = async () => {
        const oauthSources = new SourcesApi(DEFAULT_CONFIG);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                oauthSources.sourcesOauthList({ pbmUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .filter((s) => s.pagination.count > 0)
            .map((s) => s.results[0])
            .map(sourceToSelect);
    };

    return fetchAvailableOauth2Sources;
}
