import "#admin/providers/RelatedApplicationButton";
import "#admin/providers/scim/SCIMProviderForm";
import "#admin/providers/scim/SCIMProviderGroupList";
import "#admin/providers/scim/SCIMProviderUserList";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/ak-status-label";
import "#components/events/ObjectChangelog";
import "#elements/Tabs";
import "#elements/ak-mdx/index";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/ModalButton";
import "#elements/sync/SyncStatusCard";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";

import {
    ModelEnum,
    ProvidersApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    SCIMProvider,
} from "@goauthentik/api";

import MDSCIMProvider from "~docs/add-secure-apps/providers/scim/index.md";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
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
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-provider-scim-view")
export class SCIMProviderViewPage extends AKElement {
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: SCIMProvider;

    static styles: CSSResult[] = [
        PFBase,
        PFButton,
        PFBanner,
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
            .providersScimRetrieve({ id })
            .then((prov) => (this.provider = prov));
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("providerID") && this.providerID) {
            this.fetchProvider(this.providerID);
        }
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` <ak-tabs>
            <section slot="page-overview" data-tab-title="${msg("Overview")}">
                ${this.renderTabOverview()}
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${msg("Changelog")}"
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
                slot="page-users"
                data-tab-title="${msg("Provisioned Users")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <ak-provider-scim-users-list
                        providerId=${this.provider.pk}
                    ></ak-provider-scim-users-list>
                </div>
            </section>
            <section
                slot="page-groups"
                data-tab-title="${msg("Provisioned Groups")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <ak-provider-scim-groups-list
                        providerId=${this.provider.pk}
                    ></ak-provider-scim-groups-list>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikProvidersScimScimprovider}
                objectPk=${this.provider.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }

    renderTabOverview(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        const [appLabel, modelName] = ModelEnum.AuthentikProvidersScimScimprovider.split(".");
        return html` ${!this.provider?.assignedBackchannelApplicationName
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: Provider is not assigned to an application as backchannel provider.",
                      )}
                  </div>`
                : html``}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div
                    class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl"
                >
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list">
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
                                        >${msg("Assigned to application")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ak-provider-related-application
                                            mode="backchannel"
                                            .provider=${this.provider}
                                        ></ak-provider-related-application>
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
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("URL")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.url}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit"> ${msg("Update")} </span>
                            <span slot="header"> ${msg("Update SCIM Provider")} </span>
                            <ak-provider-scim-form slot="form" .instancePk=${this.provider.pk}>
                            </ak-provider-scim-form>
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
                            return new ProvidersApi(DEFAULT_CONFIG).providersScimSyncStatusRetrieve(
                                {
                                    id: this.provider?.pk || 0,
                                },
                            );
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
                <div
                    class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl"
                >
                    <div class="pf-c-card__body">
                        <ak-mdx .url=${MDSCIMProvider}></ak-mdx>
                    </div>
                </div>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-view": SCIMProviderViewPage;
    }
}
