import {
    OAuthSource,
    SourcesApi,
    FlowsApi,
    UserMatchingModeEnum,
    OAuthSourceRequest,
    FlowsInstancesListDesignationEnum,
} from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-source-oauth-form")
export class OAuthSourceForm extends ModelForm<OAuthSource, string> {
    loadInstance(pk: string): Promise<OAuthSource> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthRetrieve({
                slug: pk,
            })
            .then((source) => {
                this.showUrlOptions = first(source.type?.urlsCustomizable, false);
                return source;
            });
    }

    @property()
    modelName?: string;

    @property({ type: Boolean })
    showUrlOptions = false;

    @property({ type: Boolean })
    showRequestTokenURL = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
    }

    send = (data: OAuthSource): Promise<OAuthSource> => {
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
        if (!this.showUrlOptions) {
            return html``;
        }
        return html` <ak-form-group>
            <span slot="header"> ${t`URL settings`} </span>
            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal
                    label=${t`Authorization URL`}
                    ?required=${true}
                    name="authorizationUrl"
                >
                    <input
                        type="text"
                        value="${first(this.instance?.authorizationUrl, "")}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${t`URL the user is redirect to to consent the authorization.`}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${t`Access token URL`}
                    ?required=${true}
                    name="accessTokenUrl"
                >
                    <input
                        type="text"
                        value="${first(this.instance?.accessTokenUrl, "")}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${t`URL used by authentik to retrieve tokens.`}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${t`Profile URL`}
                    ?required=${true}
                    name="profileUrl"
                >
                    <input
                        type="text"
                        value="${first(this.instance?.profileUrl, "")}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${t`URL used by authentik to get user information.`}
                    </p>
                </ak-form-element-horizontal>
                ${this.showRequestTokenURL
                    ? html`<ak-form-element-horizontal
                          label=${t`Request token URL`}
                          name="requestTokenUrl"
                      >
                          <input
                              type="text"
                              value="${first(this.instance?.requestTokenUrl, "")}"
                              class="pf-c-form-control"
                          />
                          <p class="pf-c-form__helper-text">
                              ${t`URL used to request the initial token. This URL is only required for OAuth 1.`}
                          </p>
                      </ak-form-element-horizontal> `
                    : html``}
            </div>
        </ak-form-group>`;
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
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
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
                    <label class="pf-c-check__label"> ${t`Enabled`} </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`User matching mode`}
                ?required=${true}
                name="userMatchingMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${UserMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.Identifier}
                    >
                        ${t`Link users on unique identifier`}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${t`Link to a user with identical email address. Can have security implications when a source doesn't validate email addresses`}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${t`Use the user's email address, but deny enrollment when the email address already exists.`}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${t`Link to a user with identical username address. Can have security implications when a username is used with another source.`}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${t`Use the user's username, but deny enrollment when the username already exists.`}
                    </option>
                </select>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Consumer key`}
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
                        label=${t`Consumer secret`}
                        ?required=${true}
                        ?writeOnly=${this.instance !== undefined}
                        name="consumerSecret"
                    >
                        <input type="text" value="" class="pf-c-form-control" required />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Provider type`} name="providerType">
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const el = ev.target as HTMLSelectElement;
                                const selected = el.selectedOptions[0];
                                this.showUrlOptions = "data-urls-custom" in selected.attributes;
                                this.showRequestTokenURL =
                                    "data-request-token" in selected.attributes;
                                if (!this.instance) {
                                    this.instance = {} as OAuthSource;
                                }
                                this.instance.providerType = selected.value;
                            }}
                        >
                            ${until(
                                new SourcesApi(DEFAULT_CONFIG)
                                    .sourcesOauthSourceTypesList()
                                    .then((types) => {
                                        return types.map((type) => {
                                            let selected =
                                                this.instance?.providerType === type.slug;
                                            const modelSlug = this.modelName
                                                ?.replace("oauthsource", "")
                                                .replace("-", "");
                                            const typeSlug = type.slug.replace("-", "");
                                            if (!this.instance?.pk) {
                                                if (modelSlug === typeSlug) {
                                                    selected = true;
                                                    this.showUrlOptions = type.urlsCustomizable;
                                                    this.showRequestTokenURL =
                                                        type.requestTokenUrl !== null;
                                                }
                                            }
                                            return html`<option
                                                ?data-urls-custom=${type.urlsCustomizable}
                                                ?data-request-token=${type.requestTokenUrl}
                                                value=${type.slug}
                                                ?selected=${selected}
                                            >
                                                ${type.name}
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderUrlOptions()}
            <ak-form-group>
                <span slot="header"> ${t`Flow settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Authentication flow`}
                        ?required=${true}
                        name="authenticationFlow"
                    >
                        <select class="pf-c-form-control">
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
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
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow to use when authenticating existing users.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Enrollment flow`}
                        ?required=${true}
                        name="enrollmentFlow"
                    >
                        <select class="pf-c-form-control">
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
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
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow to use when enrolling new users.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
