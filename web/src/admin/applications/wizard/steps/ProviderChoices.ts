import "@goauthentik/admin/common/ak-license-notice";

import { TemplateResult, html } from "lit";

import type { TypeCreate } from "@goauthentik/api";

type ProviderRenderer = () => TemplateResult;

export type LocalTypeCreate = TypeCreate & {
    renderer: ProviderRenderer;
};

export const providerTypeRenderers: Record<
    string,
    { render: () => TemplateResult; order: number }
> = {
    oauth2provider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-oauth></ak-application-wizard-authentication-by-oauth>`,
        order: 90,
    },
    ldapprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`,
        order: 70,
    },
    proxyprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`,
        order: 75,
    },
    racprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-for-rac></ak-application-wizard-authentication-for-rac>`,
        order: 80,
    },
    samlprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-saml-configuration></ak-application-wizard-authentication-by-saml-configuration>`,
        order: 80,
    },
    radiusprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-radius></ak-application-wizard-authentication-by-radius>`,
        order: 70,
    },
    scimprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-scim></ak-application-wizard-authentication-by-scim>`,
        order: 60,
    },
};
