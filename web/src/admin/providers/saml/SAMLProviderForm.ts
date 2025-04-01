import { type AkCryptoCertificateSearch } from "@goauthentik/admin/common/ak-crypto-certificate-search";
import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { customElement, state } from "lit/decorators.js";

import { ProvidersApi, SAMLProvider } from "@goauthentik/api";

import { renderForm } from "./SAMLProviderFormForm.js";

@customElement("ak-provider-saml-form")
export class SAMLProviderFormPage extends BaseProviderForm<SAMLProvider> {
    @state()
    hasSigningKp = false;

    async loadInstance(pk: number): Promise<SAMLProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersSamlRetrieve({
            id: pk,
        });
        this.hasSigningKp = Boolean(provider.signingKp);
        return provider;
    }

    async send(data: SAMLProvider): Promise<SAMLProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersSamlUpdate({
                id: this.instance.pk,
                sAMLProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlCreate({
            sAMLProviderRequest: data,
        });
    }

    renderForm() {
        const setHasSigningKp = (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = Boolean(target.selectedKeypair);
        };

        return renderForm(this.instance ?? {}, [], setHasSigningKp, this.hasSigningKp);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-form": SAMLProviderFormPage;
    }
}
