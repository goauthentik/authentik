import "@goauthentik/admin/common/ak-flow-search/ak-source-flow-search";
import { iconHelperText, placeholderHelperText } from "@goauthentik/admin/helperText";
import { UserMatchingModeToLabel } from "@goauthentik/admin/sources/oauth/utils";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CapabilitiesEnum,
    FlowsInstancesListDesignationEnum,
    OAuthSource,
    OAuthSourceRequest,
    ProviderTypeEnum,
    SourceType,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

@customElement("ak-source-oauth-form")
export class OAuthSourceForm extends ModelForm<OAuthSource, string> {
    async loadInstance(pk: string): Promise<OAuthSource> {
        const source = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthRetrieve({
            slug: pk,
        });
        this.providerType = source.type;
        this.clearIcon = false;
        return source;
    }

    _modelName?: string;

    @property()
    set modelName(v: string | undefined) {
        this._modelName = v;
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthSourceTypesList({
                name: v?.replace("oauthsource", ""),
            })
            .then((type) => {
                this.providerType = type[0];
            });
    }
    get modelName(): string | undefined {
        return this._modelName;
    }

    @property({ attribute: false })
    providerType: SourceType | null = null;

    @state()
    clearIcon = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated source.");
        } else {
            return msg("Successfully created source.");
        }
    }

    async send(data: OAuthSource): Promise<OAuthSource> {
        data.providerType = (this.providerType?.slug || "") as ProviderTypeEnum;
        let source: OAuthSource;
        if (this.instance) {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthPartialUpdate({
                slug: this.instance.slug,
                patchedOAuthSourceRequest: data,
            });
        } else {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthCreate({
                oAuthSourceRequest: data as unknown as OAuthSourceRequest,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["icon"];
            if (icon || this.clearIcon) {
                await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconCreate({
                    slug: source.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconUrlCreate({
                slug: source.slug,
                filePathRequest: {
                    url: data.icon || "",
                },
            });
        }
        return source;
    }

    renderUrlOptions(): TemplateResult {
        if (!this.providerType?.urlsCustomizable) {
            return html``;
        }
        return html` <ak-form-group .expanded=${true}>
            <span slot="header"> ${msg("URL settings")} </span>
            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Authorization URL")}
                    ?required=${true}
                    name="authorizationUrl"
                >
                    <input
                        type="text"
                        value="${first(
                            this.instance?.authorizationUrl,
                            this.providerType.authorizationUrl,
                            "",
                        )}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg("URL the user is redirect to to consent the authorization.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Access token URL")}
                    ?required=${true}
                    name="accessTokenUrl"
                >
                    <input
                        type="text"
                        value="${first(
                            this.instance?.accessTokenUrl,
                            this.providerType.accessTokenUrl,
                            "",
                        )}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg("URL used by authentik to retrieve tokens.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Profile URL")}
                    ?required=${true}
                    name="profileUrl"
                >
                    <input
                        type="text"
                        value="${first(
                            this.instance?.profileUrl,
                            this.providerType.profileUrl,
                            "",
                        )}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg("URL used by authentik to get user information.")}
                    </p>
                </ak-form-element-horizontal>
                ${this.providerType.requestTokenUrl
                    ? html`<ak-form-element-horizontal
                          label=${msg("Request token URL")}
                          name="requestTokenUrl"
                      >
                          <input
                              type="text"
                              value="${first(this.instance?.requestTokenUrl, "")}"
                              class="pf-c-form-control"
                          />
                          <p class="pf-c-form__helper-text">
                              ${msg(
                                  "URL used to request the initial token. This URL is only required for OAuth 1.",
                              )}
                          </p>
                      </ak-form-element-horizontal> `
                    : html``}
                ${this.providerType.slug === ProviderTypeEnum.Openidconnect
                    ? html`
                          <ak-form-element-horizontal
                              label=${msg("OIDC Well-known URL")}
                              name="oidcWellKnownUrl"
                          >
                              <input
                                  type="text"
                                  value="${ifDefined(this.instance?.oidcWellKnownUrl)}"
                                  class="pf-c-form-control"
                              />
                              <p class="pf-c-form__helper-text">
                                  ${msg(
                                      "OIDC well-known configuration URL. Can be used to automatically configure the URLs above.",
                                  )}
                              </p>
                          </ak-form-element-horizontal>
                          <ak-form-element-horizontal
                              label=${msg("OIDC JWKS URL")}
                              name="oidcJwksUrl"
                          >
                              <input
                                  type="text"
                                  value="${ifDefined(this.instance?.oidcJwksUrl)}"
                                  class="pf-c-form-control"
                              />
                              <p class="pf-c-form__helper-text">
                                  ${msg(
                                      "JSON Web Key URL. Keys from the URL will be used to validate JWTs from this source.",
                                  )}
                              </p>
                          </ak-form-element-horizontal>

                          <ak-form-element-horizontal label=${msg("OIDC JWKS")} name="oidcJwks">
                              <ak-codemirror
                                  mode="javascript"
                                  value="${JSON.stringify(first(this.instance?.oidcJwks, {}))}"
                              >
                              </ak-codemirror>
                              <p class="pf-c-form__helper-text">${msg("Raw JWKS data.")}</p>
                          </ak-form-element-horizontal>
                      `
                    : html``}
            </div>
        </ak-form-group>`;
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Slug")} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("User matching mode")}
                ?required=${true}
                name="userMatchingMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${UserMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("User path")} name="userPathTemplate">
                <input
                    type="text"
                    value="${first(
                        this.instance?.userPathTemplate,
                        "goauthentik.io/sources/%(slug)s",
                    )}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
            </ak-form-element-horizontal>
            ${rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanSaveMedia)
                ? html`<ak-form-element-horizontal label=${msg("Icon")} name="icon">
                          <input type="file" value="" class="pf-c-form-control" />
                          ${this.instance?.icon
                              ? html`
                                    <p class="pf-c-form__helper-text">
                                        ${msg("Currently set to:")} ${this.instance?.icon}
                                    </p>
                                `
                              : html``}
                      </ak-form-element-horizontal>
                      ${this.instance?.icon
                          ? html`
                                <ak-form-element-horizontal>
                                    <label class="pf-c-switch">
                                        <input
                                            class="pf-c-switch__input"
                                            type="checkbox"
                                            @change=${(ev: Event) => {
                                                const target = ev.target as HTMLInputElement;
                                                this.clearIcon = target.checked;
                                            }}
                                        />
                                        <span class="pf-c-switch__toggle">
                                            <span class="pf-c-switch__toggle-icon">
                                                <i class="fas fa-check" aria-hidden="true"></i>
                                            </span>
                                        </span>
                                        <span class="pf-c-switch__label">
                                            ${msg("Clear icon")}
                                        </span>
                                    </label>
                                    <p class="pf-c-form__helper-text">
                                        ${msg("Delete currently set icon.")}
                                    </p>
                                </ak-form-element-horizontal>
                            `
                          : html``}`
                : html`<ak-form-element-horizontal label=${msg("Icon")} name="icon">
                      <input
                          type="text"
                          value="${first(this.instance?.icon, "")}"
                          class="pf-c-form-control"
                      />
                      <p class="pf-c-form__helper-text">${iconHelperText}</p>
                  </ak-form-element-horizontal>`}

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Consumer key")}
                        ?required=${true}
                        name="consumerKey"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.consumerKey)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Consumer secret")}
                        ?required=${true}
                        ?writeOnly=${this.instance !== undefined}
                        name="consumerSecret"
                    >
                        <textarea class="pf-c-form-control"></textarea>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Scopes")} name="additionalScopes">
                        <input
                            type="text"
                            value="${first(this.instance?.additionalScopes, "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Additional scopes to be passed to the OAuth Provider, separated by space. To replace existing scopes, prefix with *.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderUrlOptions()}
            <ak-form-group>
                <span slot="header"> ${msg("Flow settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        ?required=${true}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        ?required=${true}
                        name="enrollmentFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-enrollment"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
