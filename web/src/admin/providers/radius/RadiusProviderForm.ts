import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";

import { customElement } from "lit/decorators.js";

import { ProvidersApi, RadiusProvider } from "@goauthentik/api";

import { renderForm } from "./RadiusProviderFormForm.js";

@customElement("ak-provider-radius-form")
export class RadiusProviderFormPage extends WithBrandConfig(BaseProviderForm<RadiusProvider>) {
    loadInstance(pk: number): Promise<RadiusProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersRadiusRetrieve({
            id: pk,
        });
    }

    async send(data: RadiusProvider): Promise<RadiusProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersRadiusUpdate({
                id: this.instance.pk,
                radiusProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersRadiusCreate({
                radiusProviderRequest: data,
            });
        }
    }

    renderForm() {
        return renderForm(this.instance ?? {}, [], this.brand);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-radius-form": RadiusProviderFormPage;
    }
}
