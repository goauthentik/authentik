import { aki } from "#common/api/client";

import {
    DataProvider,
    DataProvision,
    DualSelectPair,
    DualSelectPairSource,
} from "#elements/ak-dual-select/types";

import { CertificateKeyPair, CryptoApi, KeyTypeEnum } from "@goauthentik/api";

const certToSelect = (cert: CertificateKeyPair): DualSelectPair<CertificateKeyPair> => {
    return [cert.pk, cert.name, cert.name, cert];
};

/**
 * Build a certificate {@linkcode DataProvider}, optionally restricted to certificates whose key
 * algorithm is one of `allowedKeyTypes`.
 */
export function certificateProviderFor(allowedKeyTypes?: KeyTypeEnum[]): DataProvider {
    return async (page = 1, search = ""): Promise<DataProvision> => {
        return aki(CryptoApi)
            .cryptoCertificatekeypairsList({
                ordering: "name",
                pageSize: 20,
                search: search.trim(),
                page,
                hasKey: undefined,
                keyType: allowedKeyTypes,
            })
            .then(({ pagination, results }) => {
                return {
                    pagination,
                    options: results.map(certToSelect),
                };
            });
    };
}

export const certificateProvider: DataProvider = certificateProviderFor();

export function certificateSelector(
    instanceMappings?: string[],
): DualSelectPairSource<CertificateKeyPair> {
    if (!instanceMappings) {
        return () => Promise.resolve([]);
    }

    return async () => {
        const pm = aki(CryptoApi);
        const mappings = await Promise.allSettled(
            instanceMappings.map((instanceId) =>
                pm.cryptoCertificatekeypairsRetrieve({ kpUuid: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(certToSelect);
    };
}
