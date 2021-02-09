import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { Provider } from "../../api/Providers";
import { OAuth2Provider, OAuth2SetupURLs } from "../../api/providers/OAuth2";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import { Page } from "../../elements/Page";
import { convertToTitle } from "../../utils";

@customElement("ak-provider-oauth2-view")
export class OAuth2ProviderViewPage extends Page {
    pageTitle(): string {
        return gettext(`OAuth Provider ${this.provider?.name}`);
    }
    pageDescription(): string | undefined {
        return;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    @property({type: Number})
    set providerID(value: number) {
        OAuth2Provider.get(value).then((app) => this.provider = app);
        OAuth2Provider.getLaunchURls(value).then((urls) => this.providerUrls = urls);
    }

    @property({ attribute: false })
    provider?: OAuth2Provider;

    @property({ attribute: false })
    providerUrls?: OAuth2SetupURLs;

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
                                                    ${this.provider.assigned_application_slug ?
                                                        html`<a href="#/applications/${this.provider.assigned_application_slug}">
                                                            ${this.provider.assigned_application_name}
                                                        </a>`:
                                                        html`-`
                                                    }
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Client type")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${convertToTitle(this.provider.client_type)}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Client ID")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.provider.client_id}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Redirect URIs")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.provider.redirect_uris}</div>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                                <div class="pf-c-card__footer">
                                    <ak-modal-button href="${Provider.adminUrl(`${this.provider.pk}/update/`)}">
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
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.provider_info || "-"}" />
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
                                                <span class="pf-c-form__label-text">${gettext("Userinfo Endpoint")}</span>
                                            </label>
                                            <input class="pf-c-form-control" readonly type="text" value="${this.providerUrls?.user_info || "-"}" />
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
