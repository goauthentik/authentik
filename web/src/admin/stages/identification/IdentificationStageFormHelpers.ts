import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";

import { Source, SourcesApi } from "@goauthentik/api";

const sourceToSelect = (source: Source) => [source.pk, source.name, source.name, source];

export async function sourcesProvider(page = 1, search = "") {
    const sources = await new SourcesApi(DEFAULT_CONFIG).sourcesAllList({
        ordering: "slug",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: sources.pagination,
        options: sources.results.filter((source) => source.component !== "").map(sourceToSelect),
    };
}

export function sourcesSelector(instanceSources: string[] | undefined) {
    if (!instanceSources) {
        return async (sources: DualSelectPair<Source>[]) =>
            sources.filter(([_0, _1, _2, source]: DualSelectPair<Source>) => source !== undefined);
    }
    return async () => {
        const sourcesApi = new SourcesApi(DEFAULT_CONFIG);
        const sources = await Promise.allSettled(
            instanceSources.map((instanceId) => sourcesApi.sourcesAllList({ pbmUuid: instanceId })),
        );
        return sources
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .filter((s) => s.pagination.count > 0)
            .map((s) => s.results[0])
            .map(sourceToSelect);
    };
}
