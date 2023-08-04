import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    DigestAlgorithmEnum,
    FlowsInstancesListDesignationEnum,
    PaginatedSAMLPropertyMappingList,
    PropertymappingsApi,
    PropertymappingsSamlListRequest,
    ProvidersApi,
    SAMLPropertyMapping,
    SAMLProvider,
    SignatureAlgorithmEnum,
    SpBindingEnum,
} from "@goauthentik/api";

@customElement("ak-provider-saml-form")
export class SAMLProviderFormPage extends ModelForm<SAMLProvider, number> {
    loadInstance(pk: number): Promise<SAMLProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlRetrieve({
            id: pk,
        });
    }

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsSamlList({
            ordering: "saml_name",
        });
    }

    propertyMappings?: PaginatedSAMLPropertyMappingList;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        } else {
            return msg("Successfully created provider.");
        }
    }

    async send(data: SAMLProvider): Promise<SAMLProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersSamlUpdate({
                id: this.instance.pk || 0,
                sAMLProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersSamlCreate({
                sAMLProviderRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                ?required=${false}
                name="authenticationFlow"
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${this.instance?.authenticationFlow}
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
                    .currentFlow=${this.instance?.authorizationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("ACS URL")}
                        ?required=${true}
                        name="acsUrl"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.acsUrl)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Issuer")}
                        ?required=${true}
                        name="issuer"
                    >
                        <input
                            type="text"
                            value="${this.instance?.issuer || "authentik"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">${msg("Also known as EntityID.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Service Provider Binding")}
                        ?required=${true}
                        name="spBinding"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Redirect"),
                                    value: SpBindingEnum.Redirect,
                                    default: true,
                                },
                                {
                                    label: msg("Post"),
                                    value: SpBindingEnum.Post,
                                },
                            ]}
                            .value=${this.instance?.spBinding}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Determines how authentik sends the response back to the Service Provider.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Audience")} name="audience">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.audience)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
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
                            certificate=${this.instance?.signingKp}
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
                            certificate=${this.instance?.verificationKp}
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
                                if (!this.instance?.propertyMappings) {
                                    selected =
                                        mapping.managed?.startsWith(
                                            "goauthentik.io/providers/saml",
                                        ) || false;
                                } else {
                                    selected = Array.from(this.instance?.propertyMappings).some(
                                        (su) => {
                                            return su == mapping.pk;
                                        },
                                    );
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
                        <ak-search-select
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<SAMLPropertyMapping[]> => {
                                const args: PropertymappingsSamlListRequest = {
                                    ordering: "saml_name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const items = await new PropertymappingsApi(
                                    DEFAULT_CONFIG,
                                ).propertymappingsSamlList(args);
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
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${msg("Assertion valid not before")}
                        ?required=${true}
                        name="assertionValidNotBefore"
                    >
                        <input
                            type="text"
                            value="${this.instance?.assertionValidNotBefore || "minutes=-5"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Configure the maximum allowed time drift for an assertion.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Assertion valid not on or after")}
                        ?required=${true}
                        name="assertionValidNotOnOrAfter"
                    >
                        <input
                            type="text"
                            value="${this.instance?.assertionValidNotOnOrAfter || "minutes=5"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Assertion not valid on or after current time + this value.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Session valid not on or after")}
                        ?required=${true}
                        name="sessionValidNotOnOrAfter"
                    >
                        <input
                            type="text"
                            value="${this.instance?.sessionValidNotOnOrAfter || "minutes=86400"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Session not valid on or after current time + this value.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${msg("Digest algorithm")}
                        ?required=${true}
                        name="digestAlgorithm"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: "SHA1",
                                    value: DigestAlgorithmEnum._200009Xmldsigsha1,
                                },
                                {
                                    label: "SHA256",
                                    value: DigestAlgorithmEnum._200104Xmlencsha256,
                                    default: true,
                                },
                                {
                                    label: "SHA384",
                                    value: DigestAlgorithmEnum._200104XmldsigMoresha384,
                                },
                                {
                                    label: "SHA512",
                                    value: DigestAlgorithmEnum._200104Xmlencsha512,
                                },
                            ]}
                            .value=${this.instance?.digestAlgorithm}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Signature algorithm")}
                        ?required=${true}
                        name="signatureAlgorithm"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: "RSA-SHA1",
                                    value: SignatureAlgorithmEnum._200009XmldsigrsaSha1,
                                },
                                {
                                    label: "RSA-SHA256",
                                    value: SignatureAlgorithmEnum._200104XmldsigMorersaSha256,
                                    default: true,
                                },
                                {
                                    label: "RSA-SHA384",
                                    value: SignatureAlgorithmEnum._200104XmldsigMorersaSha384,
                                },
                                {
                                    label: "RSA-SHA512",
                                    value: SignatureAlgorithmEnum._200104XmldsigMorersaSha512,
                                },
                                {
                                    label: "DSA-SHA1",
                                    value: SignatureAlgorithmEnum._200009XmldsigdsaSha1,
                                },
                            ]}
                            .value=${this.instance?.signatureAlgorithm}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
