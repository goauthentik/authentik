import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { SourcesApi } from "@goauthentik/api";

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
