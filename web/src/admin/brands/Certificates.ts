import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { CertificateKeyPair, CryptoApi } from "@goauthentik/api";

const certToSelect = (s: CertificateKeyPair) => [s.pk, s.name, s.name, s];

export async function certificateProvider(page = 1, search = "") {
    const certificates = await new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
        hasKey: undefined,
    });
    return {
        pagination: certificates.pagination,
        options: certificates.results.map(certToSelect),
    };
}

export function certificateSelector(instanceMappings?: string[]) {
    if (!instanceMappings) {
        return [];
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
