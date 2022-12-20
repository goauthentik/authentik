import "@goauthentik/admin/providers/RelatedApplicationButton";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { convertToTitle } from "@goauthentik/common/utils";
import MDProviderOAuth2 from "@goauthentik/docs/providers/oauth2/index.md";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/ObjectChangelog";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OAuth2Provider, OAuth2ProviderSetupURLs, ProvidersApi } from "@goauthentik/api";

@customElement("ak-provider-oauth2-view")
export class OAuth2ProviderViewPage extends AKElement {
    @property({ type: Number })
    set providerID(value: number) {
        const api = new ProvidersApi(DEFAULT_CONFIG);
        api.providersOauth2Retrieve({
            id: value,
        }).then((prov) => {
            this.provider = prov;
        });
        api.providersOauth2SetupUrlsRetrieve({
            id: value,
        }).then((prov) => {
            this.providerUrls = prov;
        });
    }

    @property({ attribute: false })
    provider?: OAuth2Provider;

    @property({ attribute: false })
    providerUrls?: OAuth2ProviderSetupURLs;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFGrid,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFForm,
            PFFormControl,
            PFBanner,
            AKGlobal,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` <ak-tabs>
            <section slot="page-overview" data-tab-title="${t`Overview`}">
                ${this.renderTabOverview()}
            </section>
            <section slot="page-preview" data-tab-title="${t`Preview`}">
                ${this.renderTabPreview()}
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${t`Changelog`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-object-changelog
                            targetModelPk=${this.provider?.pk || ""}
                            targetModelName=${this.provider?.metaModelName || ""}
                        >
                        </ak-object-changelog>
                    </div>
                </div>
            </section>
        </ak-tabs>`;
    }

    renderTabOverview(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` ${this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by an Application.`}
                  </div>`}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div
                    class="pf-c-card pf-l-grid__item pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                >
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${t`Name`}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.name}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${t`Assigned to application`}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ak-provider-related-application .provider=${this.provider}>
                                        </ak-provider-related-application>
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${t`Client type`}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${convertToTitle(this.provider.clientType || "")}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${t`Client ID`}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.clientId}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${t`Redirect URIs`}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.redirectUris}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit"> ${t`Update`} </span>
                            <span slot="header"> ${t`Update OAuth2 Provider`} </span>
                            <ak-provider-oauth2-form
                                slot="form"
                                .instancePk=${this.provider.pk || 0}
                            >
                            </ak-provider-oauth2-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${t`Edit`}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-7-col">
                    <div class="pf-c-card__body">
                        <form class="pf-c-form">
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text"
                                        >${t`OpenID Configuration URL`}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.providerInfo || t`-`}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text"
                                        >${t`OpenID Configuration Issuer`}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.issuer || t`-`}"
                                />
                            </div>
                            <hr />
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${t`Authorize URL`}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.authorize || t`-`}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${t`Token URL`}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.token || t`-`}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${t`Userinfo URL`}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.userInfo || t`-`}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${t`Logout URL`}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.logout || t`-`}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${t`JWKS URL`}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.jwks || t`-`}"
                                />
                            </div>
                        </form>
                    </div>
                </div>
                <div
                    class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl"
                >
                    <div class="pf-c-card__body">
                        <ak-markdown
                            .replacers=${[
                                (input: string) => {
                                    if (!this.provider) {
                                        return input;
                                    }
                                    return input.replaceAll(
                                        "&lt;application slug&gt;",
                                        this.provider.assignedApplicationSlug,
                                    );
                                },
                            ]}
                            .md=${MDProviderOAuth2}
                        ></ak-markdown>
                    </div>
                </div>
            </div>`;
    }

    renderTabPreview(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` <div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-c-card">
                <div class="pf-c-card__title">
                    ${t`Example JWT payload (for currently authenticated user)`}
                </div>
                <div class="pf-c-card__body">
                    ${until(
                        new ProvidersApi(DEFAULT_CONFIG)
                            .providersOauth2PreviewUserRetrieve({
                                id: this.provider?.pk,
                            })
                            .then((data) => {
                                return html`<pre>${JSON.stringify(data.preview, null, 4)}</pre>`;
                            }),
                    )}
                </div>
            </div>
        </div>`;
    }
}
