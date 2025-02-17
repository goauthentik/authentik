import "@goauthentik/admin/rbac/ObjectPermissionsPage";
import "@goauthentik/admin/sources/scim/SCIMSourceForm";
import "@goauthentik/admin/sources/scim/SCIMSourceGroups";
import "@goauthentik/admin/sources/scim/SCIMSourceUsers";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/buttons/TokenCopyButton";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
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

import {
    RbacPermissionsAssignedByUsersListModelEnum,
    SCIMSource,
    SourcesApi,
} from "@goauthentik/api";

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

    static get styles(): CSSResult[] {
        return [
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
            <section slot="page-overview" data-tab-title="${msg("Overview")}">
                <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
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
                                <span slot="submit"> ${msg("Update")} </span>
                                <span slot="header"> ${msg("Update SCIM Source")} </span>
                                <ak-source-scim-form slot="form" .instancePk=${this.source.slug}>
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
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${msg("Changelog")}"
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
            </section>
            <section
                slot="page-users"
                data-tab-title="${msg("Provisioned Users")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <ak-source-scim-users-list
                        sourceSlug=${this.source.slug}
                    ></ak-source-scim-users-list>
                </div>
            </section>
            <section
                slot="page-groups"
                data-tab-title="${msg("Provisioned Groups")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <ak-source-scim-groups-list
                        sourceSlug=${this.source.slug}
                    ></ak-source-scim-groups-list>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikSourcesScimScimsource}
                objectPk=${this.source.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-view": SCIMSourceViewPage;
    }
}
