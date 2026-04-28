import { renderForm } from "./RadiusProviderFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { WithBrandConfig } from "#elements/mixins/branding";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { ProvidersApi, RadiusProvider } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

/**
 * Radius Provider Form
 *
 * @prop {number} instancePk - The primary key of the instance to load.
 */
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
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersRadiusCreate({
            radiusProviderRequest: data,
        });
    }

    renderForm() {
        return renderForm({ provider: this.instance, brand: this.brand });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-radius-form": RadiusProviderFormPage;
    }
}
