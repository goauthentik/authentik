import "#admin/applications/wizard/ak-wizard-title";
import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "#admin/providers/saml/SAMLProviderFormHelpers";
import {
    digestAlgorithmOptions,
    signatureAlgorithmOptions,
} from "#admin/providers/saml/SAMLProviderOptions";

import {
    FlowsInstancesListDesignationEnum,
    PropertymappingsApi,
    type PropertymappingsProviderSamlListRequest,
    type SAMLPropertyMapping,
    type WSFederationProvider,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-application-wizard-provider-for-wsfed")
export class ApplicationWizardProviderWSFedForm extends ApplicationWizardProviderForm<WSFederationProvider> {
    label = msg("Configure WS-Federation Provider");

    @state()
    protected hasSigningKp = false;

    renderForm() {
        const provider = this.wizard.provider as WSFederationProvider;

        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                <ak-text-input
                    name="name"
                    label=${msg("Provider Name")}
                    placeholder=${msg("Type a provider name...")}
                    spellcheck="false"
                    value=${ifDefined(provider?.name)}
                    required
                ></ak-text-input>
                <ak-form-element-horizontal
                    name="authorizationFlow"
                    label=${msg("Authorization flow")}
                    required
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authorization}
                        .currentFlow=${provider?.authorizationFlow}
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when authorizing this provider.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Invalidation flow")}
                    name="invalidationFlow"
                    required
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                        .currentFlow=${provider?.invalidationFlow}
                        defaultFlowSlug="default-provider-invalidation-flow"
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when logging out of this provider.")}
                    </p>
                </ak-form-element-horizontal>

                <ak-form-group open label="${msg("Protocol settings")}">
                    <div class="pf-c-form">
                        <ak-text-input
                            name="replyUrl"
                            label=${msg("Reply URL")}
                            placeholder=${msg("https://...")}
                            input-hint="code"
                            inputmode="url"
                            value="${ifDefined(provider?.replyUrl)}"
                            required
                        ></ak-text-input>
                        <ak-text-input
                            name="wtrealm"
                            label=${msg("Realm")}
                            placeholder=${msg("")}
                            input-hint="code"
                            value="${ifDefined(provider?.wtrealm)}"
                            required
                        ></ak-text-input>
                    </div>
                </ak-form-group>

                <ak-form-group label="${msg("Advanced protocol settings")}">
                    <div class="pf-c-form">
                        <ak-form-element-horizontal
                            label=${msg("Signing Certificate")}
                            name="signingKp"
                        >
                            <ak-crypto-certificate-search
                                .certificate=${provider?.signingKp}
                                @input=${(ev: InputEvent) => {
                                    const target = ev.target as AkCryptoCertificateSearch;
                                    if (!target) return;
                                    this.hasSigningKp = !!target.selectedKeypair;
                                }}
                                singleton
                            ></ak-crypto-certificate-search>
                        </ak-form-element-horizontal>
                        ${this.hasSigningKp
                            ? html`<ak-switch-input
                                  name="signAssertion"
                                  label=${msg("Sign assertions")}
                                  ?checked=${provider?.signAssertion ?? true}
                                  help=${msg(
                                      "When enabled, the assertion element of the SAML response will be signed.",
                                  )}
                              >
                              </ak-switch-input>`
                            : nothing}

                        <ak-form-element-horizontal
                            label=${msg("Property mappings")}
                            name="propertyMappings"
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${propertyMappingsProvider}
                                .selector=${propertyMappingsSelector(provider?.propertyMappings)}
                                available-label=${msg("Available User Property Mappings")}
                                selected-label=${msg("Selected User Property Mappings")}
                            ></ak-dual-select-dynamic-selected>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${msg("NameID Property Mapping")}
                            name="nameIdMapping"
                        >
                            <ak-search-select
                                .fetchObjects=${async (
                                    query?: string,
                                ): Promise<SAMLPropertyMapping[]> => {
                                    const args: PropertymappingsProviderSamlListRequest = {
                                        ordering: "saml_name",
                                    };
                                    if (query !== undefined) {
                                        args.search = query;
                                    }
                                    const items = await new PropertymappingsApi(
                                        DEFAULT_CONFIG,
                                    ).propertymappingsProviderSamlList(args);
                                    return items.results;
                                }}
                                .renderElement=${(item: SAMLPropertyMapping): string => {
                                    return item.name;
                                }}
                                .value=${(
                                    item: SAMLPropertyMapping | undefined,
                                ): string | undefined => {
                                    return item?.pk;
                                }}
                                .selected=${(item: SAMLPropertyMapping): boolean => {
                                    return provider?.nameIdMapping === item.pk;
                                }}
                                blankable
                            >
                            </ak-search-select>
                        </ak-form-element-horizontal>

                        <ak-radio-input
                            name="digestAlgorithm"
                            label=${msg("Digest algorithm")}
                            .options=${digestAlgorithmOptions}
                            .value=${provider?.digestAlgorithm}
                            required
                        >
                        </ak-radio-input>

                        <ak-radio-input
                            name="signatureAlgorithm"
                            label=${msg("Signature algorithm")}
                            .options=${signatureAlgorithmOptions}
                            .value=${provider?.signatureAlgorithm}
                            required
                        >
                        </ak-radio-input>
                    </div>
                </ak-form-group>
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("WS-Federation Provider Step received uninitialized wizard context.");
        }
        return this.renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-wsfed": ApplicationWizardProviderWSFedForm;
    }
}
