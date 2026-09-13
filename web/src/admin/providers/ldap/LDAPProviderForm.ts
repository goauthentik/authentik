import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-branded-flow-search";

import { renderForm } from "./LDAPProviderFormForm.js";

import { aki } from "#common/api/client";

import { WithBrandConfig } from "#elements/mixins/branding";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { LDAPProvider, ProvidersApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

/**
 * LDAP Provider Form
 *
 * @prop {number} instancePk - The primary key of the instance to load.
 */
@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends WithBrandConfig(BaseProviderForm<LDAPProvider>) {
    protected endpoints = {
        load: (id: number) => aki(ProvidersApi).providersLdapRetrieve({ id }),
        create: (lDAPProviderRequest: LDAPProvider) =>
            aki(ProvidersApi).providersLdapCreate({ lDAPProviderRequest }),
        update: (id: number, lDAPProviderRequest: LDAPProvider) =>
            aki(ProvidersApi).providersLdapUpdate({ id, lDAPProviderRequest }),
    };

    renderForm() {
        return renderForm({ provider: this.instance, brand: this.brand });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ldap-form": LDAPProviderFormPage;
    }
}
