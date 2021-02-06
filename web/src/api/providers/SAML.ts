import { DefaultClient } from "../Client";
import { Provider } from "../Providers";

export class SAMLProvider extends Provider {
    acs_url: string;
    audience: string;
    issuer: string;
    assertion_valid_not_before: string;
    assertion_valid_not_on_or_after: string;
    session_valid_not_on_or_after: string;
    name_id_mapping?: string;
    digest_algorithm: string;
    signature_algorithm: string;
    signing_kp?: string;
    verification_kp?: string;

    constructor() {
        super();
        throw Error();
    }

    static get(id: number): Promise<SAMLProvider> {
        return DefaultClient.fetch<SAMLProvider>(["providers", "saml", id.toString()]);
    }

    static getMetadata(id: number): Promise<{ metadata: string }> {
        return DefaultClient.fetch(["providers", "saml", id.toString(), "metadata"]);
    }

    static appUrl(rest: string): string {
        return `/application/saml/${rest}`;
    }
}
