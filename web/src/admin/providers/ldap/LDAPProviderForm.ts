import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-branded-flow-search";

import { renderForm } from "./LDAPProviderFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

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
    async loadInstance(pk: number): Promise<LDAPProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersLdapRetrieve({
            id: pk,
        });
    }

    async send(data: LDAPProvider): Promise<LDAPProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapUpdate({
                id: this.instance.pk,
                lDAPProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersLdapCreate({
            lDAPProviderRequest: data,
        });
    }

    renderForm() {
        return renderForm({ provider: this.instance, brand: this.brand });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ldap-form": LDAPProviderFormPage;
    }
}
