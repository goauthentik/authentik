import { renderForm } from "./SCIMProviderFormForm.js";

import { aki } from "#common/api/client";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import { ProvidersApi, SCIMAuthenticationModeEnum, SCIMProvider } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-provider-scim-form")
export class SCIMProviderFormPage extends BaseProviderForm<SCIMProvider> {
    loadInstance(pk: number): Promise<SCIMProvider> {
        return aki(ProvidersApi).providersScimRetrieve({
            id: pk,
        });
    }

    async send(data: SCIMProvider): Promise<SCIMProvider> {
        if (this.instance?.pk) {
            return aki(ProvidersApi).providersScimUpdate({
                id: this.instance.pk,
                sCIMProviderRequest: data,
            });
        }
        return aki(ProvidersApi).providersScimCreate({
            sCIMProviderRequest: data,
        });
    }

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
