import "#admin/providers/RelatedApplicationButton";
import "#admin/providers/rac/ConnectionTokenList";
import "#admin/providers/rac/EndpointForm";
import "#admin/providers/rac/EndpointList";
import "#admin/providers/rac/RACProviderForm";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/ak-status-label";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import {
    ProvidersApi,
    RACProvider,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
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

@customElement("ak-provider-rac-view")
export class RACProviderViewPage extends AKElement {
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: RACProvider;

    static styles: CSSResult[] = [
        PFButton,
        PFPage,
        PFGrid,
        PFContent,
        PFList,
        PFForm,
        PFFormControl,
        PFCard,
        PFDescriptionList,
        PFBanner,
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
            .providersRacRetrieve({ id })
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
        return html`<main>
            <ak-tabs>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                >
                    ${this.renderTabOverview()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-connections"
                    id="page-connections"
                    aria-label="${msg("Connections")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-rac-connection-token-list
                                .provider=${this.provider}
                            ></ak-rac-connection-token-list>
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
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.provider?.pk || ""}
                                targetModelName=${this.provider?.metaModelName || ""}
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikProvidersRacRacprovider}
                    objectPk=${this.provider.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    renderTabOverview(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        return html`${this.provider?.assignedApplicationName
                ? nothing
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by an Application.")}
                  </div>`}
            ${this.provider?.outpostSet.length < 1
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by any Outpost.")}
                  </div>`
                : nothing}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
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
                                        >${msg("Assigned to application")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ak-provider-related-application
                                            .provider=${this.provider}
                                        ></ak-provider-related-application>
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit">${msg("Update")}</span>
                            <span slot="header">${msg("Update RAC Provider")}</span>
                            <ak-provider-rac-form slot="form" .instancePk=${this.provider.pk || 0}>
                            </ak-provider-rac-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${msg("Endpoints")}</div>
                    <div class="pf-c-card__body">
                        <ak-rac-endpoint-list .provider=${this.provider}> </ak-rac-endpoint-list>
                    </div>
                </div>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-rac-view": RACProviderViewPage;
    }
}
