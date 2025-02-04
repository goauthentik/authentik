import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import {
    oauth2ProvidersProvider,
    oauth2ProvidersSelector,
} from "@goauthentik/admin/providers/oauth2/OAuth2ProvidersProvider";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
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

        return html`<ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(provider?.name)}
                required
            ></ak-text-input>
            <ak-form-group expanded>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Signing Key")} name="signingKey">
                        <!-- NOTE: 'null' cast to 'undefined' on signingKey to satisfy Lit requirements -->
                        <ak-crypto-certificate-search
                            certificate=${ifDefined(provider?.signingKey ?? undefined)}
                            singleton
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">${msg("Key used to sign the events.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Session duration")}
                        ?required=${true}
                        name="sessionDuration"
                    >
                        <input
                            type="text"
                            value="${first(provider?.eventRetention, "days=30")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Determines how long events are stored for. If an event could not be sent correctly, its expiration is also increased by this duration.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header">${msg("Authentication settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("OIDC Providers")}
                        name="oidcAuthProviders"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${oauth2ProvidersProvider}
                            .selector=${oauth2ProvidersSelector(provider?.oidcAuthProviders)}
                            available-label=${msg("Available Providers")}
                            selected-label=${msg("Selected Providers")}
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "JWTs signed by the selected providers can be used to authenticate to this provider.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ssf-form": SSFProviderFormPage;
    }
}
