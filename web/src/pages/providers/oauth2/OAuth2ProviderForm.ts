import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    ClientTypeEnum,
    CryptoApi,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    IssuerModeEnum,
    OAuth2Provider,
    PropertymappingsApi,
    ProvidersApi,
    SourcesApi,
    SubModeEnum,
} from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import "../../../elements/utils/TimeDeltaHelp";
import { first, randomString } from "../../../utils";

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
                <select class="pf-c-form-control">
                    ${until(
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesList({
                                ordering: "slug",
                                designation: FlowsInstancesListDesignationEnum.Authorization,
                            })
                            .then((flows) => {
                                return flows.results.map((flow) => {
                                    return html`<option
                                        value=${ifDefined(flow.pk)}
                                        ?selected=${this.instance?.authorizationFlow === flow.pk}
                                    >
                                        ${flow.name} (${flow.slug})
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
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
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.signingKey === undefined}>
                                ---------
                            </option>
                            ${until(
                                new CryptoApi(DEFAULT_CONFIG)
                                    .cryptoCertificatekeypairsList({
                                        ordering: "name",
                                        hasKey: true,
                                    })
                                    .then((keys) => {
                                        return keys.results.map((key) => {
                                            let selected = this.instance?.signingKey === key.pk;
                                            if (keys.results.length === 1) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(key.pk)}
                                                ?selected=${selected}
                                            >
                                                ${key.name} (${key.privateKeyType?.toUpperCase()})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Key used to sign the tokens.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${t`Advanced protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Access token validity`}
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
                            ${t`Configure how long access tokens are valid for.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`If you are using an Implicit, client-side flow (where the token-endpoint isn't used), you probably want to increase this time.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Token validity`}
                        ?required=${true}
                        name="tokenValidity"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.tokenValidity, "days=30")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Configure how long refresh tokens and their id_tokens are valid for.`}
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
                        <select class="pf-c-form-control">
                            <option
                                value="${SubModeEnum.HashedUserId}"
                                ?selected=${this.instance?.subMode === SubModeEnum.HashedUserId}
                            >
                                ${t`Based on the Hashed User ID`}
                            </option>
                            <option
                                value="${SubModeEnum.UserUsername}"
                                ?selected=${this.instance?.subMode === SubModeEnum.UserUsername}
                            >
                                ${t`Based on the username`}
                            </option>
                            <option
                                value="${SubModeEnum.UserEmail}"
                                ?selected=${this.instance?.subMode === SubModeEnum.UserEmail}
                            >
                                ${t`Based on the User's Email. This is recommended over the UPN method.`}
                            </option>
                            <option
                                value="${SubModeEnum.UserUpn}"
                                ?selected=${this.instance?.subMode === SubModeEnum.UserUpn}
                            >
                                ${t`Based on the User's UPN, only works if user has a 'upn' attribute set. Use this method only if you have different UPN and Mail domains.`}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Configure what data should be used as unique User Identifier. For most cases, the default should be fine.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="includeClaimsInIdToken">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.includeClaimsInIdToken, true)}
                            />
                            <label class="pf-c-check__label">
                                ${t`Include claims in id_token`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${t`Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Issuer mode`}
                        ?required=${true}
                        name="issuerMode"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value="${IssuerModeEnum.PerProvider}"
                                ?selected=${this.instance?.issuerMode ===
                                IssuerModeEnum.PerProvider}
                            >
                                ${t`Each provider has a different issuer, based on the application slug.`}
                            </option>
                            <option
                                value="${IssuerModeEnum.Global}"
                                ?selected=${this.instance?.issuerMode === IssuerModeEnum.Global}
                            >
                                ${t`Same identifier is used for all providers`}
                            </option>
                        </select>
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
                            ${t`Deprecated. Instead of using this field, configure the JWKS data/URL in Sources.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`JWTs signed by certificates configured here can be used to authenticate to the provider.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Verification certificates`}
                        name="verificationKeys"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${until(
                                new CryptoApi(DEFAULT_CONFIG)
                                    .cryptoCertificatekeypairsList({
                                        ordering: "name",
                                    })
                                    .then((keys) => {
                                        return keys.results.map((key) => {
                                            const selected = (
                                                this.instance?.verificationKeys || []
                                            ).some((su) => {
                                                return su == key.pk;
                                            });
                                            return html`<option
                                                value=${key.pk}
                                                ?selected=${selected}
                                            >
                                                ${key.name} (${key.privateKeyType?.toUpperCase()})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Deprecated. Instead of using this field, configure the JWKS data/URL in Sources.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`JWTs signed by certificates configured here can be used to authenticate to the provider.`}
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
