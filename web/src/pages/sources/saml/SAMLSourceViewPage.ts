import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

import { SAMLSource, SourcesApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { EVENT_REFRESH } from "../../../constants";
import "../../../elements/CodeMirror";
import "../../../elements/Tabs";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/events/ObjectChangelog";
import "../../../elements/forms/ModalForm";
import "../../policies/BoundPoliciesList";
import "./SAMLSourceForm";

@customElement("ak-source-saml-view")
export class SAMLSourceViewPage extends LitElement {
    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesSamlRetrieve({
                slug: slug,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: SAMLSource;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFFlex,
            PFButton,
            PFDisplay,
            PFGallery,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFSizing,
            AKGlobal,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.pk) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    render(): TemplateResult {
        if (!this.source) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${t`Overview`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-u-display-flex pf-u-justify-content-center">
                    <div class="pf-u-w-75">
                        <div class="pf-c-card">
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list pf-m-3-col-on-lg">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${t`Name`}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                ${this.source.name}
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${t`SSO URL`}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                ${this.source.ssoUrl}
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${t`SLO URL`}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                ${this.source.sloUrl}
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${t`Issuer`}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                ${this.source.issuer}
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-forms-modal>
                                    <span slot="submit"> ${t`Update`} </span>
                                    <span slot="header"> ${t`Update SAML Source`} </span>
                                    <ak-source-saml-form
                                        slot="form"
                                        .instancePk=${this.source.slug}
                                    >
                                    </ak-source-saml-form>
                                    <button slot="trigger" class="pf-c-button pf-m-primary">
                                        ${t`Edit`}
                                    </button>
                                </ak-forms-modal>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${t`Changelog`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-object-changelog
                            targetModelPk=${this.source.pk || ""}
                            targetModelApp="authentik_sources_saml"
                            targetModelName="samlsource"
                        >
                        </ak-object-changelog>
                    </div>
                </div>
            </section>
            <section
                slot="page-metadata"
                data-tab-title="${t`Metadata`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-u-display-flex pf-u-justify-content-center">
                    <div class="pf-u-w-75">
                        <div class="pf-c-card">
                            ${until(
                                new SourcesApi(DEFAULT_CONFIG)
                                    .sourcesSamlMetadataRetrieve({
                                        slug: this.source.slug,
                                    })
                                    .then((m) => {
                                        return html`
                                            <div class="pf-c-card__body">
                                                <ak-codemirror
                                                    mode="xml"
                                                    ?readOnly=${true}
                                                    value="${ifDefined(m.metadata)}"
                                                ></ak-codemirror>
                                            </div>
                                            <div class="pf-c-card__footer">
                                                <a
                                                    class="pf-c-button pf-m-primary"
                                                    target="_blank"
                                                    href=${ifDefined(m.downloadUrl)}
                                                >
                                                    ${t`Download`}
                                                </a>
                                            </div>
                                        `;
                                    }),
                            )}
                        </div>
                    </div>
                </div>
            </section>
            <div
                slot="page-policy-bindings"
                data-tab-title="${t`Policy Bindings`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">
                        ${t`These bindings control which users can access this source.
                        You can only use policies here as access is checked before the user is authenticated.`}
                    </div>
                    <div class="pf-c-card__body">
                        <ak-bound-policies-list .target=${this.source.pk} ?policyOnly=${true}>
                        </ak-bound-policies-list>
                    </div>
                </div>
            </div>
        </ak-tabs>`;
    }
}
