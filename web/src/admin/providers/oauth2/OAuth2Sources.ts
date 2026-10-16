import { aki } from "#common/api/client";

import { DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";

import { OAuthSource, SourcesApi } from "@goauthentik/api";

const sourceToSelect = (source: OAuthSource): DualSelectPair<OAuthSource> => [
    source.pk,
    `${source.name} (${source.slug})`,
    source.name,
    source,
];

export async function oauth2SourcesProvider(
    page = 1,
    search = "",
    hasJwks: boolean | undefined = true,
) {
    const oauthSources = await aki(SourcesApi).sourcesOauthList({
        ordering: "name",
        hasJwks,
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: oauthSources.pagination,
        options: oauthSources.results.map(sourceToSelect),
    };
}

/** Any OAuth source, an ID-JAG's audience needn't publish a JWKS */
export const idJagSourcesProvider = (page = 1, search = "") =>
    oauth2SourcesProvider(page, search, undefined);

export function oauth2SourcesSelector(instanceMappings?: string[]): DualSelectPairSource {
    if (!instanceMappings) {
        return async () => [];
    }

    const fetchAvailableOauth2Sources: DualSelectPairSource = async () => {
        const oauthSources = aki(SourcesApi);

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
