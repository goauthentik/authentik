import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";

import { customElement } from "lit/decorators.js";

import { LDAPProvider, ProvidersApi } from "@goauthentik/api";

import { renderForm } from "./LDAPProviderFormForm.js";

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
        return renderForm(this.instance ?? {}, [], this.brand);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ldap-form": LDAPProviderFormPage;
    }
}
