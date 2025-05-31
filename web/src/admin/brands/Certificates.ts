import { DEFAULT_CONFIG } from "#common/api/config";

import {
    DataProvision,
    DualSelectPair,
    DualSelectPairSource,
} from "#elements/ak-dual-select/types";

import { CertificateKeyPair, CryptoApi } from "@goauthentik/api";

const certToSelect = (cert: CertificateKeyPair): DualSelectPair<CertificateKeyPair> => {
    return [cert.pk, cert.name, cert.name, cert];
};

export async function certificateProvider(page = 1, search = ""): Promise<DataProvision> {
    return new CryptoApi(DEFAULT_CONFIG)
        .cryptoCertificatekeypairsList({
            ordering: "name",
            pageSize: 20,
            search: search.trim(),
            page,
            hasKey: undefined,
        })
        .then(({ pagination, results }) => {
            return {
                pagination,
                options: results.map(certToSelect),
            };
        });
}

export function certificateSelector(
    instanceMappings?: string[],
): DualSelectPairSource<CertificateKeyPair> {
    if (!instanceMappings) {
        return () => Promise.resolve([]);
    }

    return async () => {
        const pm = new CryptoApi(DEFAULT_CONFIG);
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
