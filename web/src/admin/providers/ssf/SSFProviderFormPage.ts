import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { ProvidersApi, SSFProvider } from "@goauthentik/api";

/**
 * Form page for SSF Authentication Method
 *
 * @element ak-provider-ssf-form
 *
 */

@customElement("ak-provider-ssf-form")
export class SSFProviderFormPage extends BaseProviderForm<SSFProvider> {
    async loadInstance(pk: number): Promise<SSFProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersSsfRetrieve({
            id: pk,
        });
        return provider;
    }

    async send(data: SSFProvider): Promise<SSFProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersSsfUpdate({
                id: this.instance.pk,
                sSFProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersSsfCreate({
                sSFProviderRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        const provider = this.instance;

        return html` <ak-text-input
            name="name"
            label=${msg("Name")}
            value=${ifDefined(provider?.name)}
            required
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ssf-form": SSFProviderFormPage;
    }
}
