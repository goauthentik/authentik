export class AppURLManager {

    static sourceOAuth(slug: string, action: string): string {
        return `/source/oauth/${action}/${slug}/`;
    }

}
