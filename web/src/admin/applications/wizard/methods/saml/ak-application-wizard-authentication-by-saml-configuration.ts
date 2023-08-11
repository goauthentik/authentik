import "@goauthentik/admin/common/ak-core-group-search";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    PaginatedSAMLPropertyMappingList,
    PropertymappingsApi,
    SAMLProvider,
} from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";
import {
    digestAlgorithmOptions,
    signatureAlgorithmOptions,
    spBindingOptions,
} from "./SamlProviderOptions";

@customElement("ak-application-wizard-authentication-by-saml-configuration")
export class ApplicationWizardProviderSamlConfiguration extends BaseProviderPanel {
    propertyMappings?: PaginatedSAMLPropertyMappingList;

    constructor() {
        super();
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsSamlList({
                ordering: "saml_name",
            })
            .then((propertyMappings: PaginatedSAMLPropertyMappingList) => {
                this.propertyMappings = propertyMappings;
            });
    }

    render() {
        const provider = this.wizard.provider as SAMLProvider | undefined;

        return html` <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                value=${ifDefined(provider?.name)}
                required
                label=${msg("Name")}
            ></ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                ?required=${false}
                name="authenticationFlow"
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${provider?.authenticationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when a user access this provider and is not authenticated.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                label=${msg("Authorization flow")}
                ?required=${true}
                name="authorizationFlow"
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

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="acsUrl"
                        value=${ifDefined(provider?.acsUrl)}
                        required
                        label=${msg("ACS URL")}
                    ></ak-text-input>

                    <ak-text-input
                        name="issuer"
                        value=${provider?.issuer || "authentik"}
                        required
                        label=${msg("Issuer")}
                        help=${msg("Also known as EntityID.")}
                    ></ak-text-input>

                    <ak-radio-input
                        name="spBinding"
                        label=${msg("Service Provider Binding")}
                        required
                        .options=${spBindingOptions}
                        .value=${provider?.spBinding}
                        help=${msg(
                            "Determines how authentik sends the response back to the Service Provider.",
                        )}
                    >
                    </ak-radio-input>

                    <ak-text-input
                        name="audience"
                        value=${ifDefined(provider?.audience)}
                        label=${msg("Audience")}
                    ></ak-text-input>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Signing Certificate")}
                        name="signingKp"
                    >
                        <ak-crypto-certificate-search
                            certificate=${ifDefined(provider?.signingKp ?? undefined)}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Certificate used to sign outgoing Responses going to the Service Provider.",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${msg("Verification Certificate")}
                        name="verificationKp"
                    >
                        <ak-crypto-certificate-search
                            certificate=${ifDefined(provider?.verificationKp ?? undefined)}
                            nokey
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, incoming assertion's Signatures will be validated against this certificate. To allow unsigned Requests, leave on default.",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${msg("Property mappings")}
                        ?required=${true}
                        name="propertyMappings"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!provider?.propertyMappings) {
                                    selected =
                                        mapping.managed?.startsWith(
                                            "goauthentik.io/providers/saml",
                                        ) || false;
                                } else {
                                    selected = Array.from(provider?.propertyMappings).some((su) => {
                                        return su == mapping.pk;
                                    });
                                }
                                return html`<option
                                    value=${ifDefined(mapping.pk)}
                                    ?selected=${selected}
                                >
                                    ${mapping.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${msg("NameID Property Mapping")}
                        name="nameIdMapping"
                    >
                        <ak-saml-property-mapping-search
                            name="nameIdMapping"
                            propertymapping=${ifDefined(provider?.nameIdMapping ?? undefined)}
                        ></ak-saml-property-mapping-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-text-input
                        name="assertionValidNotBefore"
                        value=${provider?.assertionValidNotBefore || "minutes=-5"}
                        required
                        label=${msg("Assertion valid not before")}
                        help=${msg("Configure the maximum allowed time drift for an assertion.")}
                    ></ak-text-input>

                    <ak-text-input
                        name="assertionValidNotOnOrAfter"
                        value=${provider?.assertionValidNotOnOrAfter || "minutes=5"}
                        required
                        label=${msg("Assertion valid not on or after")}
                        help=${msg("Assertion not valid on or after current time + this value.")}
                    ></ak-text-input>

                    <ak-text-input
                        name="sessionValidNotOnOrAfter"
                        value=${provider?.sessionValidNotOnOrAfter || "minutes=86400"}
                        required
                        label=${msg("Session valid not on or after")}
                        help=${msg("Session not valid on or after current time + this value.")}
                    ></ak-text-input>

                    <ak-radio-input
                        name="digestAlgorithm"
                        label=${msg("Digest algorithm")}
                        required
                        .options=${digestAlgorithmOptions}
                        .value=${provider?.digestAlgorithm}
                    >
                    </ak-radio-input>

                    <ak-radio-input
                        name="signatureAlgorithm"
                        label=${msg("Signature algorithm")}
                        required
                        .options=${signatureAlgorithmOptions}
                        .value=${provider?.signatureAlgorithm}
                    >
                    </ak-radio-input>
                </div>
            </ak-form-group>
        </form>`;
    }
}

export default ApplicationWizardProviderSamlConfiguration;
