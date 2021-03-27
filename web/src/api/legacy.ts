export class AdminURLManager {

    static applications(rest: string): string {
        return `/administration/applications/${rest}`;
    }

    static cryptoCertificates(rest: string): string {
        return `/administration/crypto/certificates/${rest}`;
    }

    static policies(rest: string): string {
        return `/administration/policies/${rest}`;
    }

    static policyBindings(rest: string): string {
        return `/administration/policies/bindings/${rest}`;
    }

    static providers(rest: string): string {
        return `/administration/providers/${rest}`;
    }

    static propertyMappings(rest: string): string {
        return `/administration/property-mappings/${rest}`;
    }

    static outposts(rest: string): string {
        return `/administration/outposts/${rest}`;
    }

    static outpostServiceConnections(rest: string): string {
        return `/administration/outpost_service_connections/${rest}`;
    }

    static flows(rest: string): string {
        return `/administration/flows/${rest}`;
    }

    static stages(rest: string): string {
        return `/administration/stages/${rest}`;
    }

    static stagePrompts(rest: string): string {
        return `/administration/stages_prompts/${rest}`;
    }

    static stageInvitations(rest: string): string {
        return `/administration/stages/invitations/${rest}`;
    }

    static stageBindings(rest: string): string {
        return `/administration/stages/bindings/${rest}`;
    }

    static sources(rest: string): string {
        return `/administration/sources/${rest}`;
    }

    static tokens(rest: string): string {
        return `/administration/tokens/${rest}`;
    }

    static eventRules(rest: string): string {
        return `/administration/events/rules/${rest}`;
    }

    static eventTransports(rest: string): string {
        return `/administration/events/transports/${rest}`;
    }

    static users(rest: string): string {
        return `/administration/users/${rest}`;
    }

    static groups(rest: string): string {
        return `/administration/groups/${rest}`;
    }
}

export class UserURLManager {

    static tokens(rest: string): string {
        return `/-/user/tokens/${rest}`;
    }

    static authenticatorWebauthn(rest: string): string {
        return `/-/user/authenticator/webauthn/${rest}`;
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

    static configure(stageUuid: string, rest: string): string {
        return `/flows/-/configure/${stageUuid}/${rest}`;
    }

    static cancel(): string {
        return "/flows/-/cancel/";
    }

}
