import { aki } from "#common/api/client";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { LitFC } from "#elements/types";

import { AKSearchSelect, SearchSelectProps } from "#components/ak-search-select-field";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    KeyTypeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";

export interface CertificateSourceInit {
    /**
     * Allow keypairs without a private key. Otherwise they are listed but cannot be chosen.
     */
    noKey?: boolean;
    /**
     * Choose the only usable keypair when the field has no value.
     */
    singleton?: boolean;
    /**
     * Only keypairs with these key algorithms can be chosen. Others are listed but cannot be.
     */
    allowedKeyTypes?: KeyTypeEnum[];
}

/**
 * Why a keypair cannot be chosen, or `null` when it can.
 */
function formatUnusableReason(
    keypair: CertificateKeyPair,
    { noKey, allowedKeyTypes }: CertificateSourceInit,
): string | null {
    if (!noKey && !keypair.privateKeyAvailable) {
        return msg("This certificate is not a valid option here: it has no private key.", {
            id: "crypto.certificate-search.missing-private-key.description",
        });
    }

    if (
        allowedKeyTypes?.length &&
        (!keypair.keyType || !allowedKeyTypes.includes(keypair.keyType))
    ) {
        return msg("This certificate is not a valid option here: unsupported key type.", {
            id: "crypto.certificate-search.unsupported-key-type.description",
        });
    }

    return null;
}

const certificateSources = new Map<string, SearchSelectSource<CertificateKeyPair>>();

/**
 * A search select source for certificate keypairs.
 *
 * @remarks
 *   Keypairs that can't be used are still listed, last and grayed out, with the reason as their
 *   description. Sources are cached by their options, so rendering a field again passes the same
 *   source and doesn't refetch.
 */
export function certificateSource(
    init: CertificateSourceInit = {},
): SearchSelectSource<CertificateKeyPair> {
    const { noKey = false, singleton = false, allowedKeyTypes = [] } = init;
    const cacheKey = `${noKey}:${singleton}:${allowedKeyTypes.join(",")}`;
    const cached = certificateSources.get(cacheKey);

    if (cached) return cached;

    const isUsable = (keypair: CertificateKeyPair) => formatUnusableReason(keypair, init) === null;

    const restrictions: CryptoCertificatekeypairsListRequest = {
        ...(noKey ? {} : { hasKey: true }),
        ...(allowedKeyTypes.length ? { keyType: allowedKeyTypes } : {}),
    };

    const fetchObjects = async (query?: string): Promise<CertificateKeyPair[]> => {
        const args = withQuery(query, { ordering: "name" });
        const api = aki(CryptoApi);

        if (Object.keys(restrictions).length === 0) {
            const { results } = await api.cryptoCertificatekeypairsList(args);

            return results;
        }

        // The API returns one page, so ask for the usable keypairs directly. Otherwise a page
        // full of unusable ones could push the usable ones out of the list.
        const [usableResult, allResult] = await Promise.allSettled([
            api.cryptoCertificatekeypairsList({ ...args, ...restrictions }),
            api.cryptoCertificatekeypairsList(args),
        ]);

        if (usableResult.status === "rejected" && allResult.status === "rejected") {
            throw usableResult.reason;
        }

        const all = allResult.status === "fulfilled" ? allResult.value.results : [];

        const usable =
            usableResult.status === "fulfilled" ? usableResult.value.results : all.filter(isUsable);

        return [...usable, ...all.filter((keypair) => !isUsable(keypair))];
    };

    const source: SearchSelectSource<CertificateKeyPair> = {
        fetchObjects,
        keyOf: (keypair) => keypair.pk,
        labelOf: (keypair) => keypair.name,
        describe: (keypair) => formatUnusableReason(keypair, init),
        isDisabled: (keypair) => !isUsable(keypair),
        preselect: singleton
            ? (keypairs) => {
                  const usable = keypairs.filter(isUsable);

                  return usable.length === 1 ? usable[0] : undefined;
              }
            : undefined,
    };

    certificateSources.set(cacheKey, source);

    return source;
}

export type CertificateSearchProps = Omit<SearchSelectProps<CertificateKeyPair>, "source"> &
    CertificateSourceInit;

/**
 * A search select for choosing a certificate keypair.
 */
export const AKCertificateSearch: LitFC<CertificateSearchProps> = ({
    noKey,
    singleton,
    allowedKeyTypes,
    ...props
}) =>
    AKSearchSelect({
        label: msg("Certificate"),
        placeholder: msg("Select a certificate..."),
        ...props,
        source: certificateSource({ noKey, singleton, allowedKeyTypes }),
    });
