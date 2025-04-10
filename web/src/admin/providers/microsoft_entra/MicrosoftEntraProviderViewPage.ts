import "@goauthentik/admin/providers/microsoft_entra/MicrosoftEntraProviderForm";
import "@goauthentik/admin/providers/microsoft_entra/MicrosoftEntraProviderGroupList";
import "@goauthentik/admin/providers/microsoft_entra/MicrosoftEntraProviderUserList";
import "@goauthentik/admin/rbac/ObjectPermissionsPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/events/LogViewer";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, html } from "lit";
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
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    MicrosoftEntraProvider,
    ProvidersApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    SyncStatus,
} from "@goauthentik/api";

@customElement("ak-provider-microsoft-entra-view")
export class MicrosoftEntraProviderViewPage extends AKElement {
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: MicrosoftEntraProvider;

    @state()
    syncState?: SyncStatus;

    static get styles(): CSSResult[] {
        return [
            PFBase,
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
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    fetchProvider(id: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersMicrosoftEntraRetrieve({ id })
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
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                @activate=${() => {
                    new ProvidersApi(DEFAULT_CONFIG)
                        .providersMicrosoftEntraSyncStatusRetrieve({
                            id: this.provider?.pk || 0,
                        })
                        .then((state) => {
                            this.syncState = state;
                        })
                        .catch(() => {
                            this.syncState = undefined;
                        });
                }}
            >
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
                    <ak-provider-microsoft-entra-users-list
                        providerId=${this.provider.pk}
                    ></ak-provider-microsoft-entra-users-list>
                </div>
            </section>
            <section
                slot="page-groups"
                data-tab-title="${msg("Provisioned Groups")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <ak-provider-microsoft-entra-groups-list
                        providerId=${this.provider.pk}
                    ></ak-provider-microsoft-entra-groups-list>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikProvidersMicrosoftEntraMicrosoftentraprovider}
                objectPk=${this.provider.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }

    renderTabOverview(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`${!this.provider?.assignedBackchannelApplicationName
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: Provider is not assigned to an application as backchannel provider.",
                      )}
                  </div>`
                : html``}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-m-12-col pf-l-stack__item">
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
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit"> ${msg("Update")} </span>
                            <span slot="header"> ${msg("Update Microsoft Entra Provider")} </span>
                            <ak-provider-microsoft-entra-form
                                slot="form"
                                .instancePk=${this.provider.pk}
                            >
                            </ak-provider-microsoft-entra-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>

                <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                    <ak-sync-status-card
                        .fetch=${() => {
                            return new ProvidersApi(
                                DEFAULT_CONFIG,
                            ).providersMicrosoftEntraSyncStatusRetrieve({
                                id: this.provider?.pk || 0,
                            });
                        }}
                        .triggerSync=${() => {
                            return new ProvidersApi(
                                DEFAULT_CONFIG,
                            ).providersMicrosoftEntraPartialUpdate({
                                id: this.provider?.pk || 0,
                                patchedMicrosoftEntraProviderRequest: {},
                            });
                        }}
                    ></ak-sync-status-card>
                </div>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-microsoft-entra-view": MicrosoftEntraProviderViewPage;
    }
}
