import { OAuthSource, SourcesApi, FlowsApi, FlowDesignationEnum } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";

@customElement("ak-source-oauth-form")
export class OAuthSourceForm extends Form<OAuthSource> {

    set sourceSlug(value: string) {
        new SourcesApi(DEFAULT_CONFIG).sourcesOauthRead({
            slug: value,
        }).then(source => {
            this.source = source;
            this.showUrlOptions = source.type?.urlsCustomizable || false;
        });
    }

    @property({attribute: false})
    source?: OAuthSource;

    @property({type: Boolean})
    showUrlOptions = false;

    getSuccessMessage(): string {
        if (this.source) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
    }

    send = (data: OAuthSource): Promise<OAuthSource> => {
        if (this.source) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesOauthUpdate({
                slug: this.source.slug,
                data: data
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesOauthCreate({
                data: data
            });
        }
    };

    renderUrlOptions(): TemplateResult {
        if (!this.showUrlOptions) {
            return html``;
        }
        return html`
            <ak-form-group>
                <span slot="header">
                    ${t`URL settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Authorization URL`}
                        ?required=${true}
                        name="authorizationUrl">
                        <input type="text" value="${ifDefined(this.source?.authorizationUrl)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`URL the user is redirect to to consent the authorization.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Access token URL`}
                        ?required=${true}
                        name="accessTokenUrl">
                        <input type="text" value="${ifDefined(this.source?.accessTokenUrl)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`URL used by authentik to retrieve tokens.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Profile URL`}
                        ?required=${true}
                        name="profileUrl">
                        <input type="text" value="${ifDefined(this.source?.profileUrl)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`URL used by authentik to get user information.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Request token URL`}
                        name="requestTokenUrl">
                        <input type="text" value="${ifDefined(this.source?.requestTokenUrl)}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${t`URL used to request the initial token. This URL is only required for OAuth 1.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.source?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Slug`}
                ?required=${true}
                name="slug">
                <input type="text" value="${ifDefined(this.source?.slug)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.source?.enabled || true}>
                    <label class="pf-c-check__label">
                        ${t`Enabled`}
                    </label>
                </div>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Protocol settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Consumer key`}
                        ?required=${true}
                        name="consumerKey">
                        <input type="text" value="${ifDefined(this.source?.consumerKey)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Consumer secret`}
                        ?required=${true}
                        name="consumerSecret">
                        <input type="text" value="${ifDefined(this.source?.consumerSecret)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Provider type`}
                        name="providerType">
                        <select class="pf-c-form-control" @change=${(ev: Event) => {
                            const el = (ev.target as HTMLSelectElement);
                            const selected = el.selectedOptions[0];
                            if ("data-urls-custom" in selected.attributes) {
                                this.showUrlOptions = true;
                            } else {
                                this.showUrlOptions = false;
                            }
                        }}>
                            ${until(new SourcesApi(DEFAULT_CONFIG).sourcesOauthSourceTypes().then(types => {
                                return types.map(type => {
                                    return html`<option ?data-urls-custom=${type.urlsCustomizable} value=${type.slug} ?selected=${this.source?.providerType === type.slug}>${type.name}</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Keypair which is used to sign outgoing requests. Leave empty to disable signing.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderUrlOptions()}
            <ak-form-group>
                <span slot="header">
                    ${t`Flow settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Authentication flow`}
                        ?required=${true}
                        name="authenticationFlow">
                        <select class="pf-c-form-control">
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.Authentication,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    let selected = this.source?.authenticationFlow === flow.pk;
                                    if (!this.source?.authenticationFlow && flow.slug === "default-source-authentication") {
                                        selected = true;
                                    }
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Flow to use when authenticating existing users.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Enrollment flow`}
                        ?required=${true}
                        name="enrollmentFlow">
                        <select class="pf-c-form-control">
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.Enrollment,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    let selected = this.source?.enrollmentFlow === flow.pk;
                                    if (!this.source?.enrollmentFlow && flow.slug === "default-source-enrollment") {
                                        selected = true;
                                    }
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Flow to use when enrolling new users.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
