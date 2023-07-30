import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CertificateKeyPair,
    ClientTypeEnum,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    FlowsInstancesListDesignationEnum,
    IssuerModeEnum,
    OAuth2Provider,
    PaginatedOAuthSourceList,
    PaginatedScopeMappingList,
    PropertymappingsApi,
    ProvidersApi,
    SourcesApi,
    SubModeEnum,
} from "@goauthentik/api";

@customElement("ak-provider-oauth2-form")
export class OAuth2ProviderFormPage extends ModelForm<OAuth2Provider, number> {
    propertyMappings?: PaginatedScopeMappingList;
    oauthSources?: PaginatedOAuthSourceList;

    @state()
    showClientSecret = true;

    async loadInstance(pk: number): Promise<OAuth2Provider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersOauth2Retrieve({
            id: pk,
        });
        this.showClientSecret = provider.clientType === ClientTypeEnum.Confidential;
        return provider;
    }

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsScopeList({
            ordering: "scope_name",
        });
        this.oauthSources = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthList({
            ordering: "name",
            hasJwks: true,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        } else {
            return msg("Successfully created provider.");
        }
    }

    async send(data: OAuth2Provider): Promise<OAuth2Provider> {
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
                        label=${msg("Client type")}
                        ?required=${true}
                        name="clientType"
                    >
                        <ak-radio
                            @change=${(ev: CustomEvent<ClientTypeEnum>) => {
                                if (ev.detail === ClientTypeEnum.Public) {
                                    this.showClientSecret = false;
                                } else {
                                    this.showClientSecret = true;
                                }
                            }}
                            .options=${[
                                {
                                    label: msg("Confidential"),
                                    value: ClientTypeEnum.Confidential,
                                    default: true,
                                    description: html`${msg(
                                        "Confidential clients are capable of maintaining the confidentiality of their credentials such as client secrets",
                                    )}`,
                                },
                                {
                                    label: msg("Public"),
                                    value: ClientTypeEnum.Public,
                                    description: html`${msg(
                                        "Public clients are incapable of maintaining the confidentiality and should use methods like PKCE. ",
                                    )}`,
                                },
                            ]}
                            .value=${this.instance?.clientType}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Client ID")}
                        ?required=${true}
                        name="clientId"
                    >
                        <input
                            type="text"
                            value="${first(
                                this.instance?.clientId,
                                randomString(40, ascii_letters + digits),
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        ?hidden=${!this.showClientSecret}
                        label=${msg("Client Secret")}
                        name="clientSecret"
                    >
                        <input
                            type="text"
                            value="${first(
                                this.instance?.clientSecret,
                                randomString(128, ascii_letters + digits),
                            )}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Redirect URIs/Origins (RegEx)")}
                        name="redirectUris"
                    >
                        <textarea class="pf-c-form-control">
${this.instance?.redirectUris}</textarea
                        >
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Valid redirect URLs after a successful authorization flow. Also specify any origins here for Implicit flows.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If no explicit redirect URIs are specified, the first successfully used redirect URI will be saved.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                'To allow any redirect URI, set this value to ".*". Be aware of the possible security implications this can have.',
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Signing Key")} name="signingKey">
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
                        <p class="pf-c-form__helper-text">${msg("Key used to sign the tokens.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Access code validity")}
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
                            ${msg("Configure how long access codes are valid for.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Access Token validity")}
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
                            ${msg("Configure how long access tokens are valid for.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Refresh Token validity")}
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
                            ${msg("Configure how long refresh tokens are valid for.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Scopes")} name="propertyMappings">
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((scope) => {
                                let selected = false;
                                if (!this.instance?.propertyMappings) {
                                    selected =
                                        scope.managed?.startsWith(
                                            "goauthentik.io/providers/oauth2/scope-",
                                        ) || false;
                                } else {
                                    selected = Array.from(this.instance?.propertyMappings).some(
                                        (su) => {
                                            return su == scope.pk;
                                        },
                                    );
                                }
                                return html`<option
                                    value=${ifDefined(scope.pk)}
                                    ?selected=${selected}
                                >
                                    ${scope.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Select which scopes can be used by the client. The client still has to specify the scope to access the data.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Subject mode")}
                        ?required=${true}
                        name="subMode"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Based on the User's hashed ID"),
                                    value: SubModeEnum.HashedUserId,
                                    default: true,
                                },
                                {
                                    label: msg("Based on the User's ID"),
                                    value: SubModeEnum.UserId,
                                },
                                {
                                    label: msg("Based on the User's UUID"),
                                    value: SubModeEnum.UserUuid,
                                },
                                {
                                    label: msg("Based on the User's username"),
                                    value: SubModeEnum.UserUsername,
                                },
                                {
                                    label: msg("Based on the User's Email"),
                                    value: SubModeEnum.UserEmail,
                                    description: html`${msg(
                                        "This is recommended over the UPN mode.",
                                    )}`,
                                },
                                {
                                    label: msg("Based on the User's UPN"),
                                    value: SubModeEnum.UserUpn,
                                    description: html`${msg(
                                        "Requires the user to have a 'upn' attribute set, and falls back to hashed user ID. Use this mode only if you have different UPN and Mail domains.",
                                    )}`,
                                },
                            ]}
                            .value=${this.instance?.subMode}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure what data should be used as unique User Identifier. For most cases, the default should be fine.",
                            )}
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
                            <span class="pf-c-switch__label"
                                >${msg("Include claims in id_token")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Issuer mode")}
                        ?required=${true}
                        name="issuerMode"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg(
                                        "Each provider has a different issuer, based on the application slug",
                                    ),
                                    value: IssuerModeEnum.PerProvider,
                                    default: true,
                                },
                                {
                                    label: msg("Same identifier is used for all providers"),
                                    value: IssuerModeEnum.Global,
                                },
                            ]}
                            .value=${this.instance?.issuerMode}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure how the issuer field of the ID Token should be filled.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header">${msg("Machine-to-Machine authentication settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Trusted OIDC Sources")}
                        name="jwksSources"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.oauthSources?.results.map((source) => {
                                const selected = (this.instance?.jwksSources || []).some((su) => {
                                    return su == source.pk;
                                });
                                return html`<option value=${source.pk} ?selected=${selected}>
                                    ${source.name} (${source.slug})
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
