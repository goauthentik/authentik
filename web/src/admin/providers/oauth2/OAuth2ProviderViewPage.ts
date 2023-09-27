import "@goauthentik/admin/providers/RelatedApplicationButton";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { convertToTitle } from "@goauthentik/common/utils";
import "@goauthentik/components/events/ObjectChangelog";
import MDProviderOAuth2 from "@goauthentik/docs/providers/oauth2/index.md";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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

import {
    OAuth2Provider,
    OAuth2ProviderSetupURLs,
    PropertyMappingPreview,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-oauth2-view")
export class OAuth2ProviderViewPage extends AKElement {
    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersOauth2Retrieve({
                id: value,
            })
            .then((prov) => {
                this.provider = prov;
            });
    }

    @property({ attribute: false })
    provider?: OAuth2Provider;

    @state()
    providerUrls?: OAuth2ProviderSetupURLs;

    @state()
    preview?: PropertyMappingPreview;

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
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                @activate=${() => {
                    new ProvidersApi(DEFAULT_CONFIG)
                        .providersOauth2SetupUrlsRetrieve({
                            id: this.provider?.pk || 0,
                        })
                        .then((prov) => {
                            this.providerUrls = prov;
                        });
                }}
            >
                ${this.renderTabOverview()}
            </section>
            <section
                slot="page-preview"
                data-tab-title="${msg("Preview")}"
                @activate=${() => {
                    new ProvidersApi(DEFAULT_CONFIG)
                        .providersOauth2PreviewUserRetrieve({
                            id: this.provider?.pk || 0,
                        })
                        .then((preview) => (this.preview = preview));
                }}
            >
                ${this.renderTabPreview()}
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${msg("Changelog")}"
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
                      ${msg("Warning: Provider is not used by an Application.")}
                  </div>`}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div
                    class="pf-c-card pf-l-grid__item pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                >
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Name")}</span>
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
                                        >${msg("Assigned to application")}</span
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
                                        >${msg("Client type")}</span
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
                                    <span class="pf-c-description-list__text"
                                        >${msg("Client ID")}</span
                                    >
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
                                        >${msg("Redirect URIs")}</span
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
                            <span slot="submit"> ${msg("Update")} </span>
                            <span slot="header"> ${msg("Update OAuth2 Provider")} </span>
                            <ak-provider-oauth2-form
                                slot="form"
                                .instancePk=${this.provider.pk || 0}
                            >
                            </ak-provider-oauth2-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
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
                                        >${msg("OpenID Configuration URL")}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.providerInfo || msg("-")}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text"
                                        >${msg("OpenID Configuration Issuer")}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.issuer || msg("-")}"
                                />
                            </div>
                            <hr />
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text"
                                        >${msg("Authorize URL")}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.authorize || msg("-")}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${msg("Token URL")}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.token || msg("-")}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text"
                                        >${msg("Userinfo URL")}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.userInfo || msg("-")}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${msg("Logout URL")}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.logout || msg("-")}"
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${msg("JWKS URL")}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value="${this.providerUrls?.jwks || msg("-")}"
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
                    ${msg("Example JWT payload (for currently authenticated user)")}
                </div>
                <div class="pf-c-card__body">
                    ${this.preview
                        ? html`<pre>${JSON.stringify(this.preview?.preview, null, 4)}</pre>`
                        : html` <ak-empty-state ?loading=${true}></ak-empty-state> `}
                </div>
            </div>
        </div>`;
    }
}
