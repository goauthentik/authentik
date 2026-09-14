import "#elements/forms/FormGroup";

import { renderForm } from "./WSFederationProviderFormForm.js";

import { aki } from "#common/api/client";

import AkCryptoCertificateSearch from "#admin/common/ak-crypto-certificate-search";
import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { KeyTypeEnum, ProvidersApi, WSFederationProvider } from "@goauthentik/api";

import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-provider-wsfed-form")
export class WSFederationProviderForm extends BaseProviderForm<WSFederationProvider> {
    @state()
    protected hasSigningKp = false;

    @state()
    protected signingKeyType: KeyTypeEnum | null = null;

    async loadInstance(pk: number): Promise<WSFederationProvider> {
        const provider = await aki(ProvidersApi).providersWsfedRetrieve({
            id: pk,
        });
        this.hasSigningKp = !!provider.signingKp;
        return provider;
    }

    async send(data: WSFederationProvider): Promise<WSFederationProvider> {
        if (this.instance) {
            return aki(ProvidersApi).providersWsfedUpdate({
                id: this.instance.pk,
                wSFederationProviderRequest: data,
            });
        }
        return aki(ProvidersApi).providersWsfedCreate({
            wSFederationProviderRequest: data,
        });
    }

    renderForm(): TemplateResult {
        const setHasSigningKp = (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = !!target.selectedKeypair;
            this.signingKeyType = target.selectedKeypair?.keyType ?? KeyTypeEnum.Rsa;
        };

        return html`${renderForm({
            provider: this.instance ?? {},
            setHasSigningKp,
            hasSigningKp: this.hasSigningKp,
            signingKeyType: this.signingKeyType,
        })}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-wsfed-form": WSFederationProviderForm;
    }
}
