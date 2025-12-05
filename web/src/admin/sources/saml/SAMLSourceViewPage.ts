import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionsPage";
import "#admin/sources/saml/SAMLSourceForm";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { sourceBindingTypeNotices } from "#admin/sources/utils";

import {
    RbacPermissionsAssignedByUsersListModelEnum,
    SAMLMetadata,
    SAMLSource,
    SourcesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-source-saml-view")
export class SAMLSourceViewPage extends AKElement {
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

    @state()
    metadata?: SAMLMetadata;

    static styles: CSSResult[] = [
        PFBase,
        PFPage,
        PFGrid,
        PFButton,
        PFContent,
        PFCard,
        PFDescriptionList,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.pk) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    render(): SlottedTemplateResult {
        if (!this.source) {
            return nothing;
        }
        return html`<main>
            <ak-tabs>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list pf-m-3-col-on-lg">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${msg("Name")}</span
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
                                                >${msg("SSO URL")}</span
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
                                                >${msg("SLO URL")}</span
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
                                                >${msg("Issuer")}</span
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
                                    <span slot="submit">${msg("Update")}</span>
                                    <span slot="header">${msg("Update SAML Source")}</span>
                                    <ak-source-saml-form
                                        slot="form"
                                        .instancePk=${this.source.slug}
                                    >
                                    </ak-source-saml-form>
                                    <button slot="trigger" class="pf-c-button pf-m-primary">
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__body">
                                <ak-object-changelog
                                    targetModelPk=${this.source.pk || ""}
                                    targetModelApp="authentik_sources_saml"
                                    targetModelName="samlsource"
                                >
                                </ak-object-changelog>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-metadata"
                    id="page-metadata"
                    aria-label="${msg("Metadata")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    @activate=${() => {
                        new SourcesApi(DEFAULT_CONFIG)
                            .sourcesSamlMetadataRetrieve({
                                slug: this.source?.slug || "",
                            })
                            .then((metadata) => {
                                this.metadata = metadata;
                            });
                    }}
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__body">
                                <ak-codemirror
                                    mode="xml"
                                    readonly
                                    value="${ifDefined(this.metadata?.metadata)}"
                                ></ak-codemirror>
                            </div>
                            <div class="pf-c-card__footer">
                                <a
                                    class="pf-c-button pf-m-primary"
                                    target="_blank"
                                    href=${ifDefined(this.metadata?.downloadUrl)}
                                >
                                    ${msg("Download")}
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-policy-bindings"
                    id="page-policy-bindings"
                    aria-label="${msg("Policy Bindings")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__title">
                                ${msg(
                                    `These bindings control which users can access this source.
            You can only use policies here as access is checked before the user is authenticated.`,
                                )}
                            </div>
                            <div class="pf-c-card__body">
                                <ak-bound-policies-list
                                    .target=${this.source.pk}
                                    .typeNotices=${sourceBindingTypeNotices()}
                                    .policyEngineMode=${this.source.policyEngineMode}
                                >
                                </ak-bound-policies-list>
                            </div>
                        </div>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikSourcesSamlSamlsource}
                    objectPk=${this.source.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-saml-view": SAMLSourceViewPage;
    }
}
