import "#admin/providers/google_workspace/GoogleWorkspaceProviderForm";
import "#admin/providers/google_workspace/GoogleWorkspaceProviderGroupList";
import "#admin/providers/google_workspace/GoogleWorkspaceProviderUserList";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/ak-status-label";
import "#components/events/ObjectChangelog";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/ModalButton";
import "#elements/sync/SyncStatusCard";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import {
    GoogleWorkspaceProvider,
    ModelEnum,
    ProvidersApi,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

@customElement("ak-provider-google-workspace-view")
export class GoogleWorkspaceProviderViewPage extends AKElement {
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: GoogleWorkspaceProvider;

    static styles: CSSResult[] = [
        PFButton,
        PFForm,
        PFFormControl,
        PFStack,
        PFList,
        PFGrid,
        PFPage,
        PFContent,
        PFCard,
        PFDescriptionList,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    fetchProvider(id: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersGoogleWorkspaceRetrieve({ id })
            .then((prov) => (this.provider = prov));
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("providerID") && this.providerID) {
            this.fetchProvider(this.providerID);
        }
    }

    render(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        return html`<main part="main">
            <ak-tabs part="tabs">
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                >
                    ${this.renderTabOverview()}
                </section>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.provider?.pk || ""}
                                targetModelName=${this.provider?.metaModelName || ""}
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-users"
                    id="page-users"
                    aria-label="${msg("Provisioned Users")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <ak-provider-google-workspace-users-list
                            providerId=${this.provider.pk}
                        ></ak-provider-google-workspace-users-list>
                    </div>
                </section>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-groups"
                    id="page-groups"
                    aria-label="${msg("Provisioned Groups")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <ak-provider-google-workspace-groups-list
                            providerId=${this.provider.pk}
                        ></ak-provider-google-workspace-groups-list>
                    </div>
                </section>
                <ak-rbac-object-permission-page
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikProvidersGoogleWorkspaceGoogleworkspaceprovider}
                    objectPk=${this.provider.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    renderTabOverview(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        const [appLabel, modelName] =
            ModelEnum.AuthentikProvidersGoogleWorkspaceGoogleworkspaceprovider.split(".");
        return html`${!this.provider?.assignedBackchannelApplicationName
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: Provider is not assigned to an application as backchannel provider.",
                      )}
                  </div>`
                : nothing}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div
                    class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl"
                >
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-3-col-on-lg">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Name")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.name}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Dry-run")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ak-status-label
                                            ?good=${!this.provider.dryRun}
                                            type="info"
                                            good-label=${msg("No")}
                                            bad-label=${msg("Yes")}
                                        ></ak-status-label>
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit">${msg("Update")}</span>
                            <span slot="header">${msg("Update Google Workspace Provider")}</span>
                            <ak-provider-google-workspace-form
                                slot="form"
                                .instancePk=${this.provider.pk}
                            >
                            </ak-provider-google-workspace-form>
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
                            return new ProvidersApi(
                                DEFAULT_CONFIG,
                            ).providersGoogleWorkspaceSyncStatusRetrieve({
                                id: this.provider?.pk || 0,
                            });
                        }}
                    ></ak-sync-status-card>
                </div>
                <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__title">${msg("Schedules")}</div>
                        </div>
                        <div class="pf-c-card__body">
                            <ak-schedule-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${this.provider.pk}"
                            ></ak-schedule-list>
                        </div>
                    </div>
                </div>
                <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__title">${msg("Tasks")}</div>
                        </div>
                        <div class="pf-c-card__body">
                            <ak-task-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${this.provider.pk}"
                            ></ak-task-list>
                        </div>
                    </div>
                </div>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-google-workspace-view": GoogleWorkspaceProviderViewPage;
    }
}
