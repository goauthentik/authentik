import { renderForm } from "./RadiusProviderFormForm.js";

import { aki } from "#common/api/client";

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
    protected endpoints = {
        load: (id: number) => aki(ProvidersApi).providersRadiusRetrieve({ id }),
        create: (radiusProviderRequest: RadiusProvider) =>
            aki(ProvidersApi).providersRadiusCreate({ radiusProviderRequest }),
        update: (id: number, radiusProviderRequest: RadiusProvider) =>
            aki(ProvidersApi).providersRadiusUpdate({ id, radiusProviderRequest }),
    };

    renderForm() {
        return renderForm({ provider: this.instance, brand: this.brand });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-radius-form": RadiusProviderFormPage;
    }
}
