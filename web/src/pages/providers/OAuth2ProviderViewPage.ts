import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import { Page } from "../../elements/Page";
import { convertToTitle } from "../../utils";
import "./RelatedApplicationButton";
import { OAuth2Provider, OAuth2ProviderSetupURLs, ProvidersApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

@customElement("ak-provider-oauth2-view")
export class OAuth2ProviderViewPage extends Page {
    pageTitle(): string {
        return gettext(`OAuth Provider ${this.provider?.name || ""}`);
    }
    pageDescription(): string | undefined {
        return;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    @property({type: Number})
    set providerID(value: number) {
        const api = new ProvidersApi(DEFAULT_CONFIG);
        api.providersOauth2Read({
            id: value
        }).then((prov) => {
            this.provider = prov;
        });
        api.providersOauth2SetupUrls({
            id: value
        }).then((prov) => {
            this.providerUrls = prov;
        });
    }

    @property({ attribute: false })
    provider?: OAuth2Provider;

    @property({ attribute: false })
    providerUrls?: OAuth2ProviderSetupURLs;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    renderContent(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`<ak-tabs>
                <section slot="page-1" data-tab-title="${gettext("Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card pf-c-card-aggregate">
                                <div class="pf-c-card__body">
                                    <dl class="pf-c-description-list pf-m-2-col-on-lg">
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Name")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.provider.name}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Assigned to application")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    <ak-provider-related-application .provider=${this.provider}></ak-provider-related-application>
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Client type")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${convertToTitle(this.provider.clientType || "")}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Client ID")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.provider.clientId}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Redirect URIs")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.provider.redirectUris}</div>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                                <div class="pf-c-card__footer">
                                    <ak-modal-button href="${AdminURLManager.providers(`${this.provider.pk}/update/`)}">
                                        <ak-spinner-button slot="trigger" class="pf-m-primary">
                                            ${gettext("Edit")}
                                        </ak-spinner-button>
                                        <div slot="modal"></div>
                                    </ak-modal-button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section slot="page-2" data-tab-title="${gettext("Metadata")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card pf-c-card-aggregate">
                                <div class="pf-c-card__body">
                                    <form class="pf-c-form">
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label" for="help-text-simple-form-name">
                                                <span class="pf-c-form__label-text">${gettext("OpenID Configuration URL")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.providerInfo || "-"}" />
                                        </div>
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label" for="help-text-simple-form-name">
                                                <span class="pf-c-form__label-text">${gettext("OpenID Configuration Issuer")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.issuer || "-"}" />
                                        </div>
                                        <hr>
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label" for="help-text-simple-form-name">
                                                <span class="pf-c-form__label-text">${gettext("Authorize URL")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.authorize || "-"}" />
                                        </div>
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label" for="help-text-simple-form-name">
                                                <span class="pf-c-form__label-text">${gettext("Token URL")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.token || "-"}" />
                                        </div>
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label" for="help-text-simple-form-name">
                                                <span class="pf-c-form__label-text">${gettext("Userinfo URL")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.userInfo || "-"}" />
                                        </div>
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label" for="help-text-simple-form-name">
                                                <span class="pf-c-form__label-text">${gettext("Logout URL")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.logout || "-"}" />
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
