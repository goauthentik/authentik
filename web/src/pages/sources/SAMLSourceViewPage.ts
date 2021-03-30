import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import "../../elements/events/ObjectChangelog";
import { Page } from "../../elements/Page";
import { SAMLSource, SourcesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager, AppURLManager } from "../../api/legacy";
import { EVENT_REFRESH } from "../../constants";
import { ifDefined } from "lit-html/directives/if-defined";

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
        return [PFBase, PFPage, PFFlex, PFDisplay, PFGallery, PFContent, PFCard, PFDescriptionList, PFSizing, AKGlobal];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
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
                            <div class="pf-c-card">
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
                <section slot="page-2" data-tab-title="${gettext("Changelog")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.source.pk || ""}
                                targetModelApp="authentik_sources_saml"
                                targetModelName="samlsource">
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
                <section slot="page-3" data-tab-title="${gettext("Metadata")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    ${until(new SourcesApi(DEFAULT_CONFIG).sourcesSamlMetadata({
                                            slug: this.source.slug,
                                        }).then(m => {
                                            return html`<ak-codemirror mode="xml" ?readOnly=${true} value="${ifDefined(m.metadata)}"></ak-codemirror>`;
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
