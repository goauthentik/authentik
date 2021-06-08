export class AppURLManager {

    static sourceSAML(slug: string, rest: string): string {
        return `/source/saml/${slug}/${rest}`;
    }
    static sourceOAuth(slug: string, action: string): string {
        return `/source/oauth/${action}/${slug}/`;
    }

}
