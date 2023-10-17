import "@goauthentik/admin/providers/RelatedApplicationButton";
import "@goauthentik/admin/providers/radius/RadiusProviderForm";
import "@goauthentik/app/elements/rbac/ObjectPermissionsPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

import {
    ProvidersApi,
    RadiusProvider,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

@customElement("ak-provider-radius-view")
export class RadiusProviderViewPage extends AKElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersRadiusRetrieve({
                id: value,
            })
            .then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: RadiusProvider;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFDisplay,
            PFGallery,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFSizing,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                ${this.provider?.outpostSet.length < 1
                    ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                          ${msg("Warning: Provider is not used by any Outpost.")}
                      </div>`
                    : html``}
                <div class="pf-u-display-flex pf-u-justify-content-center">
                    <div class="pf-u-w-75">
                        <div class="pf-c-card">
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
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${msg("Client Networks")}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                ${this.provider.clientNetworks}
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-forms-modal>
                                    <span slot="submit"> ${msg("Update")} </span>
                                    <span slot="header"> ${msg("Update Radius Provider")} </span>
                                    <ak-provider-radius-form
                                        slot="form"
                                        .instancePk=${this.provider.pk}
                                    >
                                    </ak-provider-radius-form>
                                    <button slot="trigger" class="pf-c-button pf-m-primary">
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>
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
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-object-changelog
                            targetModelPk=${this.provider.pk || ""}
                            targetModelApp="authentik_providers_radius"
                            targetModelName="radiusprovider"
                        >
                        </ak-object-changelog>
                    </div>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.ProvidersRadiusRadiusprovider}
                objectPk=${this.provider.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}
