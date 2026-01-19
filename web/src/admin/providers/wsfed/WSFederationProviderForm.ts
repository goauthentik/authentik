import "#admin/common/ak-crypto-certificate-search";
import "#components/ak-text-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#elements/forms/Radio";

import { DEFAULT_CONFIG } from "#common/api/config";

import AkCryptoCertificateSearch from "#admin/common/ak-crypto-certificate-search";
import { BaseProviderForm } from "#admin/providers/BaseProviderForm";
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
    PropertymappingsProviderSamlListRequest,
    ProvidersApi,
    SAMLNameIDPolicyEnum,
    SAMLPropertyMapping,
    WSFederationProvider,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Form page for SSF Authentication Method
 *
 * @element ak-provider-ssf-form
 *
 */

@customElement("ak-provider-wsfed-form")
export class WSFederationProviderForm extends BaseProviderForm<WSFederationProvider> {
    @state()
    protected hasSigningKp = false;

    async loadInstance(pk: number): Promise<WSFederationProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersWsfedRetrieve({
            id: pk,
        });
        this.hasSigningKp = !!provider.signingKp;
        return provider;
    }

    async send(data: WSFederationProvider): Promise<WSFederationProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersWsfedUpdate({
                id: this.instance.pk,
                wSFederationProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersWsfedCreate({
            wSFederationProviderRequest: data,
        });
    }

    renderForm(): TemplateResult {
        const provider = this.instance;

        return html`<ak-text-input
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
                    .currentFlow=${this.instance?.authorizationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this this.instance?.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Protocol settings")}">
                <div class="pf-c-form">
                    <ak-text-input
                        name="acsUrl"
                        label=${msg("Reply URL")}
                        placeholder=${msg("https://...")}
                        input-hint="code"
                        inputmode="url"
                        value="${ifDefined(this.instance?.acsUrl)}"
                        required
                    ></ak-text-input>
                </div>
            </ak-form-group>

            <ak-form-group label="${msg("Advanced flow settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        name="authenticationFlow"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used when a user access this provider and is not authenticated.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Invalidation flow")}
                        name="invalidationFlow"
                        required
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                            .currentFlow=${this.instance?.invalidationFlow}
                            defaultFlowSlug="default-provider-invalidation-flow"
                            required
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow used when logging out of this this.instance?.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group label="${msg("Advanced protocol settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Signing Certificate")}
                        name="signingKp"
                    >
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.signingKp}
                            @input=${(ev: InputEvent) => {
                                const target = ev.target as AkCryptoCertificateSearch;
                                if (!target) return;
                                this.hasSigningKp = !!target.selectedKeypair;
                            }}
                            singleton
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Certificate used to sign outgoing Responses going to the Service this.instance?.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.hasSigningKp
                        ? html`<ak-switch-input
                                  name="signAssertion"
                                  label=${msg("Sign assertions")}
                                  ?checked=${this.instance?.signAssertion ?? true}
                                  help=${msg(
                                      "When enabled, the assertion element of the SAML response will be signed.",
                                  )}
                              >
                              </ak-switch-input>
                              <ak-switch-input
                                  name="signLogoutRequest"
                                  label=${msg("Sign logout requests")}
                                  ?checked=${this.instance?.signLogoutRequest ?? false}
                                  help=${msg("When enabled, SAML logout requests will be signed.")}
                              >
                              </ak-switch-input>`
                        : nothing}

                    <ak-form-element-horizontal
                        label=${msg("Verification Certificate")}
                        name="verificationKp"
                    >
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.verificationKp}
                            nokey
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, incoming assertion's Signatures will be validated against this certificate. To allow unsigned Requests, leave on default.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Encryption Certificate")}
                        name="encryptionKp"
                    >
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.encryptionKp}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, assertions will be encrypted using this keypair.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Property mappings")}
                        name="propertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(this.instance?.propertyMappings)}
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
                                return this.instance?.nameIdMapping === item.pk;
                            }}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("AuthnContextClassRef Property Mapping")}
                        name="authnContextClassRefMapping"
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
                                return this.instance?.authnContextClassRefMapping === item.pk;
                            }}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure how the AuthnContextClassRef value will be created. When left empty, the AuthnContextClassRef will be set based on which authentication methods the user used to authenticate.",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-text-input
                        name="sessionValidNotOnOrAfter"
                        label=${msg("Session valid not on or after")}
                        value="${this.instance?.sessionValidNotOnOrAfter || "minutes=86400"}"
                        required
                        help=${msg("Session not valid on or after current time + this value.")}
                    ></ak-text-input>
                    <ak-form-element-horizontal
                        label=${msg("Default NameID Policy")}
                        required
                        name="defaultNameIdPolicy"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                                ?selected=${provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                            >
                                ${msg("Persistent")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                                ?selected=${provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                            >
                                ${msg("Email address")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                                ?selected=${provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                            >
                                ${msg("Windows")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                                ?selected=${provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                            >
                                ${msg("X509 Subject")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                                ?selected=${provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                            >
                                ${msg("Transient")}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure the default NameID Policy used by IDP-initiated logins and when an incoming assertion doesn't specify a NameID Policy (also applies when using a custom NameID Mapping).",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-radio-input
                        name="digestAlgorithm"
                        label=${msg("Digest algorithm")}
                        .options=${digestAlgorithmOptions}
                        .value=${this.instance?.digestAlgorithm}
                        required
                    >
                    </ak-radio-input>

                    <ak-radio-input
                        name="signatureAlgorithm"
                        label=${msg("Signature algorithm")}
                        .options=${signatureAlgorithmOptions}
                        .value=${this.instance?.signatureAlgorithm}
                        required
                    >
                    </ak-radio-input>
                </div>
            </ak-form-group> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-wsfed-form": WSFederationProviderForm;
    }
}
