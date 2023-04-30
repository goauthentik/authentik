import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    DigestAlgorithmEnum,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
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
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
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
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authentication flow`}
                ?required=${false}
                name="authenticationFlow"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Authentication,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
                        return flows.results;
                    }}
                    .renderElement=${(flow: Flow): string => {
                        return RenderFlowOption(flow);
                    }}
                    .renderDescription=${(flow: Flow): TemplateResult => {
                        return html`${flow.name}`;
                    }}
                    .value=${(flow: Flow | undefined): string | undefined => {
                        return flow?.pk;
                    }}
                    .selected=${(flow: Flow): boolean => {
                        return flow.pk === this.instance?.authenticationFlow;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used when a user access this provider and is not authenticated.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Authorization,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
                        return flows.results;
                    }}
                    .renderElement=${(flow: Flow): string => {
                        return RenderFlowOption(flow);
                    }}
                    .renderDescription=${(flow: Flow): TemplateResult => {
                        return html`${flow.name}`;
                    }}
                    .value=${(flow: Flow | undefined): string | undefined => {
                        return flow?.pk;
                    }}
                    .selected=${(flow: Flow): boolean => {
                        return flow.pk === this.instance?.authorizationFlow;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used when authorizing this provider.`}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`ACS URL`} ?required=${true} name="acsUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.acsUrl)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Issuer`} ?required=${true} name="issuer">
                        <input
                            type="text"
                            value="${this.instance?.issuer || "authentik"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">${t`Also known as EntityID.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Service Provider Binding`}
                        ?required=${true}
                        name="spBinding"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: t`Redirect`,
                                    value: SpBindingEnum.Redirect,
                                    default: true,
                                },
                                {
                                    label: t`Post`,
                                    value: SpBindingEnum.Post,
                                },
                            ]}
                            .value=${this.instance?.spBinding}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${t`Determines how authentik sends the response back to the Service Provider.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Audience`} name="audience">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.audience)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${t`Advanced protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Signing Certificate`} name="signingKp">
                        <ak-search-select
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<CertificateKeyPair[]> => {
                                const args: CryptoCertificatekeypairsListRequest = {
                                    ordering: "name",
                                    hasKey: true,
                                    includeDetails: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const certificates = await new CryptoApi(
                                    DEFAULT_CONFIG,
                                ).cryptoCertificatekeypairsList(args);
                                return certificates.results;
                            }}
                            .renderElement=${(item: CertificateKeyPair): string => {
                                return item.name;
                            }}
                            .value=${(item: CertificateKeyPair | undefined): string | undefined => {
                                return item?.pk;
                            }}
                            .selected=${(item: CertificateKeyPair): boolean => {
                                return item.pk === this.instance?.signingKp;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Certificate used to sign outgoing Responses going to the Service Provider.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Verification Certificate`}
                        name="verificationKp"
                    >
                        <ak-search-select
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<CertificateKeyPair[]> => {
                                const args: CryptoCertificatekeypairsListRequest = {
                                    ordering: "name",
                                    includeDetails: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const certificates = await new CryptoApi(
                                    DEFAULT_CONFIG,
                                ).cryptoCertificatekeypairsList(args);
                                return certificates.results;
                            }}
                            .renderElement=${(item: CertificateKeyPair): string => {
                                return item.name;
                            }}
                            .value=${(item: CertificateKeyPair | undefined): string | undefined => {
                                return item?.pk;
                            }}
                            .selected=${(item: CertificateKeyPair): boolean => {
                                return item.pk === this.instance?.verificationKp;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`When selected, incoming assertion's Signatures will be validated against this certificate. To allow unsigned Requests, leave on default.`}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${t`Property mappings`}
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
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`NameID Property Mapping`}
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
                            ${t`Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.`}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${t`Assertion valid not before`}
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
                            ${t`Configure the maximum allowed time drift for an assertion.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Assertion valid not on or after`}
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
                            ${t`Assertion not valid on or after current time + this value.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Session valid not on or after`}
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
                            ${t`Session not valid on or after current time + this value.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${t`Digest algorithm`}
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
                        label=${t`Signature algorithm`}
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
