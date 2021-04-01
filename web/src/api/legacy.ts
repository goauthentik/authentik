export class AdminURLManager {

    static policies(rest: string): string {
        return `/administration/policies/${rest}`;
    }

    static stages(rest: string): string {
        return `/administration/stages/${rest}`;
    }

    static sources(rest: string): string {
        return `/administration/sources/${rest}`;
    }

}

export class AppURLManager {

    static sourceSAML(slug: string, rest: string): string {
        return `/source/saml/${slug}/${rest}`;
    }
    static sourceOAuth(slug: string, action: string): string {
        return `/source/oauth/${action}/${slug}/`;
    }
    static providerSAML(rest: string): string {
        return `/application/saml/${rest}`;
    }

}

export class FlowURLManager {

    static defaultUnenrollment(): string {
        return "/flows/-/default/unenrollment/";
    }

    static configure(stageUuid: string, rest: string): string {
        return `/flows/-/configure/${stageUuid}/${rest}`;
    }

    static cancel(): string {
        return "/flows/-/cancel/";
    }

}
