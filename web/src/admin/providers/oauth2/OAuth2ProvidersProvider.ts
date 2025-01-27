import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";

import { OAuth2Provider, ProvidersApi } from "@goauthentik/api";

const providerToSelect = (provider: OAuth2Provider) => [provider.pk, provider.name];

export async function oauth2ProvidersProvider(page = 1, search = "") {
    const oauthProviders = await new ProvidersApi(DEFAULT_CONFIG).providersOauth2List({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: oauthProviders.pagination,
        options: oauthProviders.results.map((provider) => providerToSelect(provider)),
    };
}

export function oauth2ProvidersSelector(instanceProviders: number[] | undefined) {
    if (!instanceProviders) {
        return async (mappings: DualSelectPair<OAuth2Provider>[]) =>
            mappings.filter(
                ([_0, _1, _2, source]: DualSelectPair<OAuth2Provider>) => source !== undefined,
            );
    }

    return async () => {
        const oauthSources = new ProvidersApi(DEFAULT_CONFIG);
        const mappings = await Promise.allSettled(
            instanceProviders.map((instanceId) =>
                oauthSources.providersOauth2Retrieve({ id: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(providerToSelect);
    };
}
