import { DefaultClient } from "../Client";
import { Provider } from "../Providers";

export interface OAuth2SetupURLs {

    issuer?: string;
    authorize: string;
    token: string;
    user_info: string;
    provider_info?: string;

}

export class OAuth2Provider extends Provider {
    client_type: string
    client_id: string;
    client_secret: string;
    token_validity: string;
    include_claims_in_id_token: boolean;
    jwt_alg: string;
    rsa_key: string;
    redirect_uris: string;
    sub_mode: string;
    issuer_mode: string;

    constructor() {
        super();
        throw Error();
    }

    static get(id: number): Promise<OAuth2Provider> {
        return DefaultClient.fetch<OAuth2Provider>(["providers", "oauth2", id.toString()]);
    }

    static getLaunchURls(id: number): Promise<OAuth2SetupURLs> {
        return DefaultClient.fetch(["providers", "oauth2", id.toString(), "setup_urls"]);
    }

    static appUrl(rest: string): string {
        return `/application/oauth2/${rest}`;
    }
}
