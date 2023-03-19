import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    CertificateKeyPair,
    ClientTypeEnum,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    IssuerModeEnum,
    OAuth2Provider,
    PropertymappingsApi,
    ProvidersApi,
    SourcesApi,
    SubModeEnum,
} from "@goauthentik/api";

@customElement("ak-provider-oauth2-form")
export class OAuth2ProviderFormPage extends ModelForm<OAuth2Provider, number> {
    loadInstance(pk: number): Promise<OAuth2Provider> {
        return new ProvidersApi(DEFAULT_CONFIG)
            .providersOauth2Retrieve({
                id: pk,
            })
            .then((provider) => {
                this.showClientSecret = provider.clientType === ClientTypeEnum.Confidential;
                return provider;
            });
    }

    @property({ type: Boolean })
    showClientSecret = true;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    send = (data: OAuth2Provider): Promise<OAuth2Provider> => {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersOauth2Update({
                id: this.instance.pk || 0,
                oAuth2ProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersOauth2Create({
                oAuth2ProviderRequest: data,
            });
        }
    };

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
                    <ak-form-element-horizontal
                        label=${t`Client type`}
                        ?required=${true}
                        name="clientType"
                    >
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const target = ev.target as HTMLSelectElement;
                                if (target.selectedOptions[0].value === ClientTypeEnum.Public) {
                                    this.showClientSecret = false;
                                } else {
                                    this.showClientSecret = true;
                                }
                            }}
                        >
                            <option
                                value=${ClientTypeEnum.Confidential}
                                ?selected=${this.instance?.clientType ===
                                ClientTypeEnum.Confidential}
                            >
                                ${t`Confidential`}
                            </option>
                            <option
                                value=${ClientTypeEnum.Public}
                                ?selected=${this.instance?.clientType === ClientTypeEnum.Public}
                            >
                                ${t`Public`}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Confidential clients are capable of maintaining the confidentiality of their credentials. Public clients are incapable.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Client ID`}
                        ?required=${true}
                        name="clientId"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientId, randomString(40))}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        ?hidden=${!this.showClientSecret}
                        label=${t`Client Secret`}
                        name="clientSecret"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientSecret, randomString(128))}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Redirect URIs/Origins (RegEx)`}
                        name="redirectUris"
                    >
                        <textarea class="pf-c-form-control">
${this.instance?.redirectUris}</textarea
                        >
                        <p class="pf-c-form__helper-text">
                            ${t`Valid redirect URLs after a successful authorization flow. Also specify any origins here for Implicit flows.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`If no explicit redirect URIs are specified, the first successfully used redirect URI will be saved.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`To allow any redirect URI, set this value to ".*". Be aware of the possible security implications this can have.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Signing Key`} name="signingKey">
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
                            .selected=${(
                                item: CertificateKeyPair,
                                items: CertificateKeyPair[],
                            ): boolean => {
                                let selected = this.instance?.signingKey === item.pk;
                                if (!this.instance && items.length === 1) {
                                    selected = true;
                                }
                                return selected;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">${t`Key used to sign the tokens.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${t`Advanced protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Access code validity`}
                        ?required=${true}
                        name="accessCodeValidity"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.accessCodeValidity, "minutes=1")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Configure how long access codes are valid for.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Access Token validity`}
                        ?required=${true}
                        name="accessTokenValidity"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.accessTokenValidity, "minutes=5")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Configure how long access tokens are valid for.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Refresh Token validity`}
                        ?required=${true}
                        name="refreshTokenValidity"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.refreshTokenValidity, "days=30")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Configure how long refresh tokens are valid for.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Scopes`} name="propertyMappings">
                        <select class="pf-c-form-control" multiple>
                            ${until(
                                new PropertymappingsApi(DEFAULT_CONFIG)
                                    .propertymappingsScopeList({
                                        ordering: "scope_name",
                                    })
                                    .then((scopes) => {
                                        return scopes.results.map((scope) => {
                                            let selected = false;
                                            if (!this.instance?.propertyMappings) {
                                                selected =
                                                    scope.managed?.startsWith(
                                                        "goauthentik.io/providers/oauth2/scope-",
                                                    ) || false;
                                            } else {
                                                selected = Array.from(
                                                    this.instance?.propertyMappings,
                                                ).some((su) => {
                                                    return su == scope.pk;
                                                });
                                            }
                                            return html`<option
                                                value=${ifDefined(scope.pk)}
                                                ?selected=${selected}
                                            >
                                                ${scope.name}
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Select which scopes can be used by the client. The client still has to specify the scope to access the data.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Subject mode`}
                        ?required=${true}
                        name="subMode"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: t`Based on the User's hashed ID`,
                                    value: SubModeEnum.HashedUserId,
                                    default: true,
                                },
                                {
                                    label: t`Based on the User's ID`,
                                    value: SubModeEnum.UserId,
                                },
                                {
                                    label: t`Based on the User's username`,
                                    value: SubModeEnum.UserUsername,
                                },
                                {
                                    label: t`Based on the User's Email`,
                                    value: SubModeEnum.UserEmail,
                                    description: html`${t`This is recommended over the UPN mode.`}`,
                                },
                                {
                                    label: t`Based on the User's UPN`,
                                    value: SubModeEnum.UserUpn,
                                    description: html`${t`Requires the user to have a 'upn' attribute set, and falls back to hashed user ID. Use this mode only if you have different UPN and Mail domains.`}`,
                                },
                            ]}
                            .value=${this.instance?.subMode}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${t`Configure what data should be used as unique User Identifier. For most cases, the default should be fine.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="includeClaimsInIdToken">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.includeClaimsInIdToken, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Include claims in id_token`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Issuer mode`}
                        ?required=${true}
                        name="issuerMode"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: t`Each provider has a different issuer, based on the application slug`,
                                    value: IssuerModeEnum.PerProvider,
                                    default: true,
                                },
                                {
                                    label: t`Same identifier is used for all providers`,
                                    value: IssuerModeEnum.Global,
                                },
                            ]}
                            .value=${this.instance?.issuerMode}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${t`Configure how the issuer field of the ID Token should be filled.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header">${t`Machine-to-Machine authentication settings`}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Trusted OIDC Sources`} name="jwksSources">
                        <select class="pf-c-form-control" multiple>
                            ${until(
                                new SourcesApi(DEFAULT_CONFIG)
                                    .sourcesOauthList({
                                        ordering: "name",
                                        hasJwks: true,
                                    })
                                    .then((sources) => {
                                        return sources.results.map((source) => {
                                            const selected = (
                                                this.instance?.jwksSources || []
                                            ).some((su) => {
                                                return su == source.pk;
                                            });
                                            return html`<option
                                                value=${source.pk}
                                                ?selected=${selected}
                                            >
                                                ${source.name} (${source.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
