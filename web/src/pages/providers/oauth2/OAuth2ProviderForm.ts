import { CryptoApi, FlowDesignationEnum, FlowsApi, OAuth2Provider, OAuth2ProviderClientTypeEnum, OAuth2ProviderIssuerModeEnum, OAuth2ProviderJwtAlgEnum, OAuth2ProviderSubModeEnum, PropertymappingsApi, ProvidersApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";

@customElement("ak-provider-oauth2-form")
export class OAuth2ProviderFormPage extends Form<OAuth2Provider> {

    set providerUUID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG).providersOauth2Read({
            id: value,
        }).then(provider => {
            this.provider = provider;
        });
    }

    @property({attribute: false})
    provider?: OAuth2Provider;

    getSuccessMessage(): string {
        if (this.provider) {
            return gettext("Successfully updated provider.");
        } else {
            return gettext("Successfully created provider.");
        }
    }

    send = (data: OAuth2Provider): Promise<OAuth2Provider> => {
        if (this.provider) {
            return new ProvidersApi(DEFAULT_CONFIG).providersOauth2Update({
                id: this.provider.pk || 0,
                data: data
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersOauth2Create({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.provider?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Authorization flow")}
                ?required=${true}
                name="authorizationFlow">
                <select class="pf-c-form-control">
                    ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                        ordering: "pk",
                        designation: FlowDesignationEnum.Authorization,
                    }).then(flows => {
                        return flows.results.map(flow => {
                            return html`<option value=${ifDefined(flow.pk)} ?selected=${this.provider?.authorizationFlow === flow.pk}>${flow.name} (${flow.slug})</option>`;
                        });
                    }))}
                </select>
                <p class="pf-c-form__helper-text">${gettext("Flow used when authorizing this provider.")}</p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                label=${gettext("Client type")}
                ?required=${true}
                name="clientType">
                <select class="pf-c-form-control">
                    <option value=${OAuth2ProviderClientTypeEnum.Confidential} ?selected=${this.provider?.clientType === OAuth2ProviderClientTypeEnum.Confidential}>
                        ${gettext("Confidential")}
                    </option>
                    <option value=${OAuth2ProviderClientTypeEnum.Public} ?selected=${this.provider?.clientType === OAuth2ProviderClientTypeEnum.Public}>
                        ${gettext("Public")}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">${gettext("Confidential clients are capable of maintaining the confidentiality of their credentials. Public clients are incapable.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Client ID")}
                ?required=${true}
                name="clientId">
                <input type="text" value="${ifDefined(this.provider?.clientId)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Client Secret")}
                name="clientSecret">
                <input type="text" value="${ifDefined(this.provider?.clientSecret /* TODO: Generate secret */)}" class="pf-c-form-control">
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Token validity")}
                ?required=${true}
                name="tokenValidity">
                <input type="text" value="${this.provider?.tokenValidity || "minutes=10"}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("JWT Algorithm")}
                ?required=${true}
                name="jwtAlg">
                <select class="pf-c-form-control">
                    <option value=${OAuth2ProviderJwtAlgEnum.Rs256} ?selected=${this.provider?.jwtAlg === OAuth2ProviderJwtAlgEnum.Rs256}>
                        ${gettext("RS256 (Asymmetric Encryption)")}
                    </option>
                    <option value=${OAuth2ProviderJwtAlgEnum.Hs256} ?selected=${this.provider?.jwtAlg === OAuth2ProviderJwtAlgEnum.Hs256}>
                        ${gettext("HS256 (Symmetric Encryption)")}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">${gettext("Algorithm used to sign the JWT Tokens.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Scopes")}
                ?required=${true}
                name="propertyMappings">
                <select class="pf-c-form-control" multiple>
                    ${until(new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScopeList({
                        ordering: "scope_name"
                    }).then(scopes => {
                        return scopes.results.map(scope => {
                            const selected = Array.from(this.provider?.propertyMappings || []).some(su => {
                                return su == scope.pk;
                            });
                            return html`<option value=${ifDefined(scope.pk)} ?selected=${selected}>${scope.name}</option>`;
                        });
                    }))}
                </select>
                <p class="pf-c-form__helper-text">${gettext("Select which scopes can be used by the client. The client stil has to specify the scope to access the data.")}</p>
                <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("RSA Key")}
                ?required=${true}
                name="rsaKey">
                <select class="pf-c-form-control">
                    ${until(new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList({
                        ordering: "pk",
                        hasKey: "true",
                    }).then(keys => {
                        return keys.results.map(key => {
                            return html`<option value=${ifDefined(key.pk)} ?selected=${this.provider?.rsaKey === key.pk}>${key.name}</option>`;
                        });
                    }))}
                </select>
                <p class="pf-c-form__helper-text">${gettext("Key used to sign the tokens. Only required when JWT Algorithm is set to RS256.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Redirect URIs")}
                name="redirectUris">
                <textarea class="pf-c-form-control">${this.provider?.redirectUris}</textarea>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Subject mode")}
                ?required=${true}
                name="subMode">
                <select class="pf-c-form-control">
                    <option value="${OAuth2ProviderSubModeEnum.HashedUserId}" ?selected=${this.provider?.subMode === OAuth2ProviderSubModeEnum.HashedUserId}>
                        ${gettext("Based on the Hashed User ID")}
                    </option>
                    <option value="${OAuth2ProviderSubModeEnum.UserUsername}" ?selected=${this.provider?.subMode === OAuth2ProviderSubModeEnum.UserUsername}>
                        ${gettext("Based on the username")}
                    </option>
                    <option value="${OAuth2ProviderSubModeEnum.UserEmail}" ?selected=${this.provider?.subMode === OAuth2ProviderSubModeEnum.UserEmail}>
                        ${gettext("Based on the User's Email. This is recommended over the UPN method.")}
                    </option>
                    <option value="${OAuth2ProviderSubModeEnum.UserUpn}" ?selected=${this.provider?.subMode === OAuth2ProviderSubModeEnum.UserUpn}>
                        ${gettext("Based on the User's UPN, only works if user has a 'upn' attribute set. Use this method only if you have different UPN and Mail domains.")}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">
                    ${gettext("Configure what data should be used as unique User Identifier. For most cases, the default should be fine.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="includeClaimsInIdToken">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.provider?.includeClaimsInIdToken || false}>
                    <label class="pf-c-check__label">
                        ${gettext("Include claims in id_token")}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${gettext("Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Issuer mode")}
                ?required=${true}
                name="issuerMode">
                <select class="pf-c-form-control">
                    <option value="${OAuth2ProviderIssuerModeEnum.PerProvider}" ?selected=${this.provider?.issuerMode === OAuth2ProviderIssuerModeEnum.PerProvider}>
                        ${gettext("Each provider has a different issuer, based on the application slug.")}
                    </option>
                    <option value="${OAuth2ProviderIssuerModeEnum.Global}" ?selected=${this.provider?.issuerMode === OAuth2ProviderIssuerModeEnum.Global}>
                        ${gettext("Same identifier is used for all providers")}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">
                    ${gettext("Configure how the issuer field of the ID Token should be filled.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
