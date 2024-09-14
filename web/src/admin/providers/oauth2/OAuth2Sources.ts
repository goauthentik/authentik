import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";

import { OAuthSource, SourcesApi } from "@goauthentik/api";

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
        options: oauthSources.results.map((source) => [
            source.pk,
            `${source.name} (${source.slug})`,
        ]),
    };
}

export function makeSourceSelector(instanceSources: string[] | undefined) {
    const localSources = instanceSources ? new Set(instanceSources) : undefined;

    return localSources
        ? ([pk, _]: DualSelectPair) => localSources.has(pk)
        : ([_0, _1, _2, prompt]: DualSelectPair<OAuthSource>) => prompt !== undefined;
}
