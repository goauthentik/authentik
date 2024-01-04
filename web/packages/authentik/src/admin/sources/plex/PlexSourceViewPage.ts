import "@goauthentik/admin/policies/BoundPoliciesList";
import "@goauthentik/admin/sources/plex/PlexSourceForm";
import "@goauthentik/app/elements/rbac/ObjectPermissionsPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    PlexSource,
    RbacPermissionsAssignedByUsersListModelEnum,
    SourcesApi,
} from "@goauthentik/api";

@customElement("ak-source-plex-view")
export class PlexSourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(value: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesPlexRetrieve({
                slug: value,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: PlexSource;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFButton, PFGrid, PFContent, PFCard, PFDescriptionList];
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
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
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
                            </dl>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-forms-modal>
                                <span slot="submit"> ${msg("Update")} </span>
                                <span slot="header"> ${msg("Update Plex Source")} </span>
                                <ak-source-plex-form slot="form" .instancePk=${this.source.slug}>
                                </ak-source-plex-form>
                                <button slot="trigger" class="pf-c-button pf-m-primary">
                                    ${msg("Edit")}
                                </button>
                            </ak-forms-modal>
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
                                targetModelApp="authentik_sources_plex"
                                targetModelName="plexsource"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </section>
            <div
                slot="page-policy-binding"
                data-tab-title="${msg("Policy Bindings")}"
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
                            <ak-bound-policies-list .target=${this.source.pk} ?policyOnly=${true}>
                            </ak-bound-policies-list>
                        </div>
                    </div>
                </div>
            </div>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.SourcesPlexPlexsource}
                objectPk=${this.source.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}
