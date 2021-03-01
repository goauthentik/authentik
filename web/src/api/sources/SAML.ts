import { DefaultClient } from "../Client";
import { Source } from "../Sources";

export class SAMLSource extends Source {
    issuer: string;
    sso_url: string;
    slo_url: string;
    allow_idp_initiated: boolean;
    name_id_policy: string;
    binding_type: string
    signing_kp?: string;
    digest_algorithm: string;
    signature_algorithm: string;
    temporary_user_delete_after: string;

    constructor() {
        super();
        throw Error();
    }

    static get(slug: string): Promise<SAMLSource> {
        return DefaultClient.fetch<SAMLSource>(["sources", "saml", slug]);
    }

    static getMetadata(slug: string): Promise<{ metadata: string }> {
        return DefaultClient.fetch(["sources", "saml", slug, "metadata"]);
    }

    static appUrl(slug: string, rest: string): string {
        return `/source/saml/${slug}/${rest}`;
    }
}
