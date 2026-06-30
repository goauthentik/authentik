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
 * @property {number} instancePk - The primary key of the instance to load.
 */
@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends WithBrandConfig(BaseProviderForm<LDAPProvider>) {
    async loadInstance(pk: number): Promise<LDAPProvider> {
        return aki(ProvidersApi).providersLdapRetrieve({
            id: pk,
        });
    }

    async send(data: LDAPProvider): Promise<LDAPProvider> {
        if (this.instance) {
            return aki(ProvidersApi).providersLdapUpdate({
                id: this.instance.pk,
                lDAPProviderRequest: data,
            });
        }

        return aki(ProvidersApi).providersLdapCreate({
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
