import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";

import { customElement } from "lit/decorators.js";

import { ProvidersApi, SCIMProvider } from "@goauthentik/api";

import { renderForm } from "./SCIMProviderFormForm.js";

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
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersScimCreate({
                sCIMProviderRequest: data,
            });
        }
    }

    renderForm() {
        return renderForm(this.instance ?? {}, []);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-form": SCIMProviderFormPage;
    }
}
