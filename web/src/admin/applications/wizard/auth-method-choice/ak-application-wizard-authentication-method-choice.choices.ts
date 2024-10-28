import "@goauthentik/admin/common/ak-license-notice";

import { TemplateResult, html } from "lit";

import type { TypeCreate } from "@goauthentik/api";

type ProviderRenderer = () => TemplateResult;

export type LocalTypeCreate = TypeCreate & {
    renderer: ProviderRenderer;
};

export const providerTypeRenderers = {
    oauth2provider: () =>
        html`<ak-application-wizard-authentication-by-oauth></ak-application-wizard-authentication-by-oauth>`,
    ldapprovider: () =>
        html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`,
    proxyprovider: () =>
        html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`,
    racprovider: () =>
        html`<ak-application-wizard-authentication-for-rac></ak-application-wizard-authentication-for-rac>`,
    samlprovider: () =>
        html`<ak-application-wizard-authentication-by-saml-configuration></ak-application-wizard-authentication-by-saml-configuration>`,
    radiusprovider: () =>
        html`<ak-application-wizard-authentication-by-radius></ak-application-wizard-authentication-by-radius>`,
    scimprovider: () =>
        html`<ak-application-wizard-authentication-by-scim></ak-application-wizard-authentication-by-scim>`,
};
