import "#admin/common/ak-license-notice";

import type { TypeCreate } from "@goauthentik/api";

import { html, TemplateResult } from "lit";

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
        order: 95,
    },
    samlprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-saml-configuration></ak-application-wizard-authentication-by-saml-configuration>`,
        order: 90,
    },
    samlproviderimportmodel: {
        render: () =>
            html`<ak-application-wizard-authentication-by-saml-metadata-configuration></ak-application-wizard-authentication-by-saml-metadata-configuration>`,
        order: 85,
    },
    racprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-for-rac></ak-application-wizard-authentication-for-rac>`,
        order: 80,
    },
    proxyprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`,
        order: 75,
    },
    radiusprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-radius></ak-application-wizard-authentication-by-radius>`,
        order: 70,
    },
    ldapprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`,
        order: 65,
    },
    scimprovider: {
        render: () =>
            html`<ak-application-wizard-authentication-by-scim></ak-application-wizard-authentication-by-scim>`,
        order: 60,
    },
};
