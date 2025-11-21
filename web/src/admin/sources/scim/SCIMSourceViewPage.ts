import "#admin/rbac/ObjectPermissionsPage";
import "#admin/sources/scim/SCIMSourceForm";
import "#admin/sources/scim/SCIMSourceGroups";
import "#admin/sources/scim/SCIMSourceUsers";
import "#components/events/ObjectChangelog";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/buttons/TokenCopyButton/index";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import {
    RbacPermissionsAssignedByRolesListModelEnum,
    SCIMSource,
    SourcesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-source-scim-view")
export class SCIMSourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(value: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesScimRetrieve({
                slug: value,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: SCIMSource;

    static styles: CSSResult[] = [
        PFBase,
        PFPage,
        PFButton,
        PFForm,
        PFFormControl,
        PFGrid,
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
                >
                    <div
                        class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
                    >
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list pf-m-2-col-on-lg">
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
                                                >${msg("Slug")}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                ${this.source.slug}
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-forms-modal>
                                    <span slot="submit">${msg("Update")}</span>
                                    <span slot="header">${msg("Update SCIM Source")}</span>
                                    <ak-source-scim-form
                                        slot="form"
                                        .instancePk=${this.source.slug}
                                    >
                                    </ak-source-scim-form>
                                    <button slot="trigger" class="pf-c-button pf-m-primary">
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <form class="pf-c-form">
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label">
                                                <span class="pf-c-form__label-text"
                                                    >${msg("SCIM Base URL")}</span
                                                >
                                            </label>
                                            <input
                                                class="pf-c-form-control"
                                                readonly
                                                type="text"
                                                value="${this.source.rootUrl}"
                                            />
                                        </div>
                                        <div class="pf-c-form__group">
                                            <label class="pf-c-form__label">
                                                <span class="pf-c-form__label-text"
                                                    >${msg("Token")}</span
                                                >
                                            </label>
                                            <div>
                                                <ak-token-copy-button
                                                    class="pf-m-primary"
                                                    identifier="${this.source?.tokenObj.identifier}"
                                                >
                                                    ${msg("Click to copy token")}
                                                </ak-token-copy-button>
                                            </div>
                                        </div>
                                    </form>
                                </div>
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
                                    targetModelApp="authentik_sources_scim"
                                    targetModelName="scimsource"
                                >
                                </ak-object-changelog>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-users"
                    id="page-users"
                    aria-label="${msg("Provisioned Users")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <ak-source-scim-users-list
                            sourceSlug=${this.source.slug}
                        ></ak-source-scim-users-list>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-groups"
                    id="page-groups"
                    aria-label="${msg("Provisioned Groups")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <ak-source-scim-groups-list
                            sourceSlug=${this.source.slug}
                        ></ak-source-scim-groups-list>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikSourcesScimScimsource}
                    objectPk=${this.source.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-view": SCIMSourceViewPage;
    }
}
