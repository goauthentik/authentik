import { DefaultClient } from "../Client";
import { Source } from "../Sources";

export class OAuthSource extends Source {
    provider_type: string;
    request_token_url: string;
    authorization_url: string;
    access_token_url: string;
    profile_url: string;
    consumer_key: string;
    callback_url: string;

    constructor() {
        super();
        throw Error();
    }

    static get(slug: string): Promise<OAuthSource> {
        return DefaultClient.fetch<OAuthSource>(["sources", "oauth", slug]);
    }

}
