import { renderForm } from "./SCIMProviderFormForm.js";

import { aki } from "#common/api/client";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { ProvidersApi, SCIMAuthenticationModeEnum, SCIMProvider } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-provider-scim-form")
export class SCIMProviderFormPage extends BaseProviderForm<SCIMProvider> {
    protected endpoints = {
        load: (id: number) => aki(ProvidersApi).providersScimRetrieve({ id }),
        create: (sCIMProviderRequest: SCIMProvider) =>
            aki(ProvidersApi).providersScimCreate({ sCIMProviderRequest }),
        update: (id: number, sCIMProviderRequest: SCIMProvider) =>
            aki(ProvidersApi).providersScimUpdate({ id, sCIMProviderRequest }),
    };

    public override createDefaultInstance(): SCIMProvider {
        return {
            authMode: SCIMAuthenticationModeEnum.Token,
        } as SCIMProvider;
    }

    renderForm() {
        return renderForm({
            update: this.requestUpdate.bind(this),
            provider: this.instance,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-form": SCIMProviderFormPage;
    }
}
