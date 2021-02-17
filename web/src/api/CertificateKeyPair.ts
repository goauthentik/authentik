import { DefaultClient, AKResponse, QueryArguments } from "./Client";

export class CertificateKeyPair {
    pk: string;
    name: string;
    fingerprint: string;
    cert_expiry: number;
    cert_subject: string;
    private_key_available: boolean;

    constructor() {
        throw Error();
    }

    static get(slug: string): Promise<CertificateKeyPair> {
        return DefaultClient.fetch<CertificateKeyPair>(["crypto", "certificatekeypairs", slug]);
    }

    static list(filter?: QueryArguments): Promise<AKResponse<CertificateKeyPair>> {
        return DefaultClient.fetch<AKResponse<CertificateKeyPair>>(["crypto", "certificatekeypairs"], filter);
    }

    static adminUrl(rest: string): string {
        return `/administration/crypto/certificates/${rest}`;
    }
}
