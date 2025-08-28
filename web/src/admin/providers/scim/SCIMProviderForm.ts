import { renderForm } from "./SCIMProviderFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { ProvidersApi, SCIMProvider } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-provider-scim-form")
export class SCIMProviderFormPage extends BaseProviderForm<SCIMProvider> {
    loadInstance(pk: number): Promise<SCIMProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimRetrieve({
            id: pk,
        });
    }

    async send(data: SCIMProvider): Promise<SCIMProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersScimUpdate({
                id: this.instance.pk,
                sCIMProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersScimCreate({
            sCIMProviderRequest: data,
        });
    }

    renderForm() {
        return renderForm({ provider: this.instance });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-form": SCIMProviderFormPage;
    }
}
