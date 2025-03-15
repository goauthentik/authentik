import "@goauthentik/admin/rbac/ObjectPermissionsPage";
import "@goauthentik/admin/sources/kerberos/KerberosSourceConnectivity";
import "@goauthentik/admin/sources/kerberos/KerberosSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { EVENT_REFRESH } from "@goauthentik/common/constants.js";
import "@goauthentik/components/events/ObjectChangelog";
import MDSourceKerberosBrowser from "@goauthentik/docs/users-sources/sources/protocols/kerberos/browser.md";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/SyncStatusCard";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    KerberosSource,
    RbacPermissionsAssignedByUsersListModelEnum,
    SourcesApi,
    SyncStatus,
} from "@goauthentik/api";

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

    @state()
    syncState?: SyncStatus;

    static get styles(): CSSResult[] {
        return [
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
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.slug) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    load(): void {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesKerberosSyncStatusRetrieve({
                slug: this.source.slug,
            })
            .then((state) => {
                this.syncState = state;
            });
    }

    renderSyncCards(): TemplateResult {
        if (!this.source.syncUsers) {
            return html``;
        }
        return html`
            <div class="pf-c-card pf-l-grid__item pf-m-2-col">
                <div class="pf-c-card__title">
                    <p>${msg("Connectivity")}</p>
                </div>
                <div class="pf-c-card__body">
                    <ak-source-kerberos-connectivity
                        .connectivity=${this.source.connectivity}
                    ></ak-source-kerberos-connectivity>
                </div>
            </div>
            <div class="pf-l-grid__item pf-m-10-col">
                <ak-sync-status-card
                    .fetch=${() => {
                        return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosSyncStatusRetrieve({
                            slug: this.source?.slug,
                        });
                    }}
                    .triggerSync=${() => {
                        return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosPartialUpdate({
                            slug: this.source?.slug || "",
                            patchedKerberosSourceRequest: {},
                        });
                    }}
                ></ak-sync-status-card>
            </div>
        `;
    }

    render(): TemplateResult {
        if (!this.source) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
                @activate=${() => {
                    this.load();
                }}
            >
                <div slot="header" class="pf-c-banner pf-m-info">
                    ${msg("Kerberos Source is in preview.")}
                    <a href="mailto:hello+feature/kerberos-source@goauthentik.io"
                        >${msg("Send us feedback!")}</a
                    >
                </div>
                <div class="pf-l-grid pf-m-gutter">
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
                    ${this.renderSyncCards()}
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__body">
                            <ak-markdown
                                .md=${MDSourceKerberosBrowser}
                                meta="users-sources/protocols/kerberos/browser.md"
                                ;
                            ></ak-markdown>
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
