import "#admin/rbac/ObjectPermissionsPage";
import "#admin/sources/kerberos/KerberosSourceConnectivity";
import "#admin/sources/kerberos/KerberosSourceForm";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/ak-mdx/index";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncStatusCard";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";

import {
    KerberosSource,
    ModelEnum,
    RbacPermissionsAssignedByUsersListModelEnum,
    SourcesApi,
} from "@goauthentik/api";

import MDSourceKerberosBrowser from "~docs/users-sources/sources/protocols/kerberos/browser.md";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-source-kerberos-view")
export class KerberosSourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesKerberosRetrieve({
                slug: slug,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source!: KerberosSource;

    static styles: CSSResult[] = [
        PFBase,
        PFPage,
        PFButton,
        PFGrid,
        PFContent,
        PFCard,
        PFDescriptionList,
        PFBanner,
        PFList,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.slug) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    render(): TemplateResult {
        if (!this.source) {
            return html``;
        }
        const [appLabel, modelName] = ModelEnum.AuthentikSourcesKerberosKerberossource.split(".");
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div slot="header" class="pf-c-banner pf-m-info">
                    ${msg("Kerberos Source is in preview.")}
                    <a href="mailto:hello+feature/kerberos-source@goauthentik.io"
                        >${msg("Send us feedback!")}</a
                    >
                </div>
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl"
                    >
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
                                            >${msg("Realm")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.source.realm}
                                        </div>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-forms-modal>
                                <span slot="submit"> ${msg("Update")} </span>
                                <span slot="header"> ${msg("Update Kerberos Source")} </span>
                                <ak-source-kerberos-form
                                    slot="form"
                                    .instancePk=${this.source.slug}
                                >
                                </ak-source-kerberos-form>
                                <button slot="trigger" class="pf-c-button pf-m-primary">
                                    ${msg("Edit")}
                                </button>
                            </ak-forms-modal>
                        </div>
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl"
                    >
                        <ak-sync-status-card
                            .fetch=${() => {
                                return new SourcesApi(
                                    DEFAULT_CONFIG,
                                ).sourcesKerberosSyncStatusRetrieve({
                                    slug: this.source?.slug,
                                });
                            }}
                        ></ak-sync-status-card>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">
                            <p>${msg("Connectivity")}</p>
                        </div>
                        <div class="pf-c-card__body">
                            <ak-source-kerberos-connectivity
                                .connectivity=${this.source.connectivity}
                            ></ak-source-kerberos-connectivity>
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">
                            <p>${msg("Schedules")}</p>
                        </div>
                        <div class="pf-c-card__body">
                            <ak-schedule-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${this.source.pk}"
                            ></ak-schedule-list>
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__body">
                            <ak-mdx .url=${MDSourceKerberosBrowser}></ak-mdx>
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
                                targetModelApp="authentik_sources_kerberos"
                                targetModelName="kerberossource"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikSourcesKerberosKerberossource}
                objectPk=${this.source.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-kerberos-view": KerberosSourceViewPage;
    }
}
