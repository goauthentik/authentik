import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import { Page } from "../../elements/Page";
import { SAMLSource, SourcesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager, AppURLManager } from "../../api/legacy";

@customElement("ak-source-saml-view")
export class SAMLSourceViewPage extends Page {
    pageTitle(): string {
        return gettext(`SAML Source ${this.source?.name || ""}`);
    }
    pageDescription(): string | undefined {
        return;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG).sourcesSamlRead({
            slug: slug
        }).then((source) => {
            this.source = source;
        });
    }

    @property({ attribute: false })
    source?: SAMLSource;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            if (!this.source?.pk) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    renderContent(): TemplateResult {
        if (!this.source) {
            return html``;
        }
        return html`<ak-tabs>
                <section slot="page-1" data-tab-title="${gettext("Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card pf-c-card-aggregate">
                                <div class="pf-c-card__body">
                                    <dl class="pf-c-description-list pf-m-3-col-on-lg">
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Name")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.source.name}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("SSO URL")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.source.ssoUrl}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("SLO URL")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.source.sloUrl}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Issuer")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.source.issuer}</div>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                                <div class="pf-c-card__footer">
                                    <ak-modal-button href="${AdminURLManager.sources(`${this.source.pk}/update/`)}">
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
                                    ${until(new SourcesApi(DEFAULT_CONFIG).sourcesSamlMetadata({
                                            slug: this.source.slug,
                                        }).then(m => {
                                            return html`<ak-codemirror mode="xml"><textarea class="pf-c-form-control" readonly>${m.metadata}</textarea></ak-codemirror>`;
                                        })
                                    )}
                                </div>
                                <div class="pf-c-card__footer">
                                    <a class="pf-c-button pf-m-primary" target="_blank" href="${AppURLManager.sourceSAML(this.source.slug, "metadata/")}">
                                        ${gettext("Download")}
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
