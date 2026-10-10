import "#elements/forms/FormGroup";
import { renderForm } from "./WSFederationProviderFormForm.js";

import { aki } from "#common/api/client";

import type { SearchSelectChangeEvent } from "#elements/forms/SearchSelect/events";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import {
    KeyTypeEnum,
    ProvidersApi,
    WSFederationProvider,
    CertificateKeyPair,
} from "@goauthentik/api";

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
        const setHasSigningKp = ({ detail }: SearchSelectChangeEvent<CertificateKeyPair>) => {
            this.hasSigningKp = !!detail.value;
            this.signingKeyType = detail.value?.keyType ?? KeyTypeEnum.Rsa;
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
