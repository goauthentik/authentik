import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    FlowsApi,
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
    loadInstance(pk: string): Promise<OAuthSource> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthRetrieve({
                slug: pk,
            })
            .then((source) => {
                this.providerType = source.type;
                return source;
            });
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

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated source.");
        } else {
            return msg("Successfully created source.");
        }
    }

    send = (data: OAuthSource): Promise<OAuthSource> => {
        data.providerType = (this.providerType?.slug || "") as ProviderTypeEnum;
        if (this.instance?.slug) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesOauthPartialUpdate({
                slug: this.instance.slug,
                patchedOAuthSourceRequest: data,
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesOauthCreate({
                oAuthSourceRequest: data as unknown as OAuthSourceRequest,
            });
        }
    };

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
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
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
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${msg("Enabled")} </label>
                </div>
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
                        ${msg("Link users on unique identifier")}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${msg(
                            "Link to a user with identical email address. Can have security implications when a source doesn't validate email addresses",
                        )}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${msg(
                            "Use the user's email address, but deny enrollment when the email address already exists.",
                        )}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${msg(
                            "Link to a user with identical username. Can have security implications when a username is used with another source.",
                        )}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${msg(
                            "Use the user's username, but deny enrollment when the username already exists.",
                        )}
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
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Path template for users created. Use placeholders like `%(slug)s` to insert the source slug.",
                    )}
                </p>
            </ak-form-element-horizontal>

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
                    <ak-form-element-horizontal
                        label=${msg("Additional Scope")}
                        name="additionalScopes"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.additionalScopes, "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Additional scopes to be passed to the OAuth Provider, separated by space.",
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
                        <select class="pf-c-form-control">
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation:
                                            FlowsInstancesListDesignationEnum.Authentication,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.authenticationFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.authenticationFlow &&
                                                flow.slug === "default-source-authentication"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        ?required=${true}
                        name="enrollmentFlow"
                    >
                        <select class="pf-c-form-control">
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation: FlowsInstancesListDesignationEnum.Enrollment,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.enrollmentFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.enrollmentFlow &&
                                                flow.slug === "default-source-enrollment"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
