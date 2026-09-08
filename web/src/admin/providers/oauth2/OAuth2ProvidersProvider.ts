import { aki } from "#common/api/client";

import { DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";

import { OAuth2Provider, ProvidersApi } from "@goauthentik/api";

const providerToSelect = (provider: OAuth2Provider): DualSelectPair<OAuth2Provider> => [
    provider.pk,
    provider.name,
    provider.name,
    provider,
];

export async function oauth2ProvidersProvider(page = 1, search = "") {
    const oauthProviders = await aki(ProvidersApi).providersOauth2List({
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

export function oauth2ProvidersSelector(
    instanceProviders: number[] | undefined,
): DualSelectPairSource {
    if (!instanceProviders) {
        return async () => [];
    }

    const fetchOauth2Providers: DualSelectPairSource = async () => {
        const oauthSources = aki(ProvidersApi);
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

    return fetchOauth2Providers;
}
