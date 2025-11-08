import "#admin/common/ak-license-notice";

import { ProviderModelSuffix } from "#admin/applications/wizard/steps/providers/shared";

import type { TypeCreate } from "@goauthentik/api";

import { html, TemplateResult } from "lit";

type ProviderRenderer = () => TemplateResult;

export interface WizardReadyTypeCreate extends TypeCreate {
    modelName: WizardReadyProviderSuffix;
}

export interface LocalTypeCreate extends TypeCreate {
    renderer: ProviderRenderer;
    modelName: WizardReadyProviderSuffix;
}

export interface ProviderRendererInit {
    render: ProviderRenderer;
    order: number;
}

export const WizardProviderRenderRecord = {
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
} as const satisfies {
    [key in ProviderModelSuffix]?: ProviderRendererInit;
};

export type WizardReadyProviderSuffix = keyof typeof WizardProviderRenderRecord;

export const WizardReadyProviders = new Set(
    Object.keys(WizardProviderRenderRecord),
) as ReadonlySet<WizardReadyProviderSuffix>;

export function isWizardReadyProvider(value?: string | null): value is WizardReadyProviderSuffix {
    return WizardReadyProviders.has(value as WizardReadyProviderSuffix);
}

export function isWizardReadyTypeCreate(creatable: TypeCreate): creatable is WizardReadyTypeCreate {
    return isWizardReadyProvider(creatable.modelName);
}
