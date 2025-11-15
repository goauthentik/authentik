import "#admin/providers/RelatedApplicationButton";
import "#admin/providers/ldap/LDAPProviderForm";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";
import { SlottedTemplateResult } from "#elements/types";

import {
    LDAPProvider,
    ProvidersApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-provider-ldap-view")
export class LDAPProviderViewPage extends WithSession(AKElement) {
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: LDAPProvider;

    static styles: CSSResult[] = [
        PFBase,
        PFButton,
        PFBanner,
        PFForm,
        PFFormControl,
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
            .providersLdapRetrieve({ id })
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
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikProvidersLdapLdapprovider}
                    objectPk=${this.provider.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    renderTabOverview(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }

        return html`
            ${
                this.provider?.outpostSet.length < 1
                    ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                          ${msg("Warning: Provider is not used by any Outpost.")}
                      </div>`
                    : nothing
            }
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
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Base DN")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.baseDn}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit">${msg("Update")}</span>
                            <span slot="header">${msg("Update LDAP Provider")}</span>
                            <ak-provider-ldap-form slot="form" .instancePk=${this.provider.pk}>
                            </ak-provider-ldap-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">
                        ${msg("How to connect")}
                    </div>
                    <div class="pf-c-card__body">
                        <p>
                            ${msg("Connect to the LDAP Server on port 389:")}
                        </p>
                        <ul class="pf-c-list">
                            <li>${msg("Check the IP of the Kubernetes service, or")}</li>
                            <li>${msg("The Host IP of the docker host")}</li>
                        </ul>
                        <form class="pf-c-form">
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${msg("Bind DN")}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value=${`cn=${this.currentUser?.username},ou=users,${this.provider?.baseDn?.toLowerCase()}`}
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${msg(
                                        "Bind Password",
                                    )}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value=${msg("Your authentik password")}
                                />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text">${msg("Search base")}</span>
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value=${ifDefined(this.provider?.baseDn?.toLowerCase())}
                                />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ldap-view": LDAPProviderViewPage;
    }
}
