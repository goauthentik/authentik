import "#admin/providers/RelatedApplicationButton";
import "#admin/providers/ssf/StreamTable";
import "#admin/events/ObjectChangelog";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/CodeMirror";
import "#elements/EmptyState";
import "#elements/Tabs";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";
import "#elements/tasks/TaskList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import { SSFProviderFormPage } from "#admin/providers/ssf/SSFProviderFormPage";

import { ModelEnum, ProvidersApi, SSFProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-provider-ssf-view")
export class SSFProviderViewPage extends AKElement {
    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersSsfRetrieve({
                id: value,
            })
            .then((prov) => {
                this.provider = prov;
            });
    }

    @property({ attribute: false })
    provider?: SSFProvider;

    static styles: CSSResult[] = [
        PFButton,
        PFPage,
        PFGrid,
        PFCard,
        PFDescriptionList,
        PFForm,
        PFFormControl,
        PFList,
        PFList,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
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
                        <ak-object-changelog
                            targetModelPk=${this.provider?.pk || ""}
                            targetModelName=${this.provider?.metaModelName || ""}
                        >
                        </ak-object-changelog>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${ModelEnum.AuthentikProvidersSsfSsfprovider}
                    objectPk=${this.provider.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    renderTabOverview(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        const [appLabel, modelName] = ModelEnum.AuthentikProvidersSsfSsfprovider.split(".");
        return html`<div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-4-col-on-xl pf-m-4-col-on-2xl">
                <div class="pf-c-card__body">
                    ${renderDescriptionList([
                        [msg("Name"), html`${this.provider.name}`],
                        [
                            msg("URL"),
                            html`<input
                                class="pf-c-form-control pf-m-monospace"
                                readonly
                                type="text"
                                value=${this.provider.ssfUrl || ""}
                                placeholder=${this.provider.ssfUrl
                                    ? msg("SSF URL")
                                    : msg("No assigned application")}
                            />`,
                        ],
                        [
                            msg("Federated OAuth2/OpenID Providers"),
                            (this.provider.oidcAuthProvidersObj || []).length > 0
                                ? html`<ul class="pf-c-list">
                                      ${this.provider.oidcAuthProvidersObj.map((provider) => {
                                          return html`
                                              <li>
                                                  <a href="#/core/providers/${provider.pk}">
                                                      ${provider.name}
                                                  </a>
                                              </li>
                                          `;
                                      })}
                                  </ul>`
                                : html`-`,
                        ],
                        [
                            msg("Related actions"),
                            html`<button
                                class="pf-c-button pf-m-primary pf-m-block"
                                ${modalInvoker(SSFProviderFormPage, {
                                    instancePk: this.provider.pk,
                                })}
                            >
                                ${msg("Edit")}
                            </button>`,
                        ],
                    ])}
                </div>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-8-col-on-2xl">
                <div class="pf-c-card__title">${msg("Streams")}</div>
                <ak-provider-ssf-stream-list .providerId=${this.providerID}>
                </ak-provider-ssf-stream-list>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col-on-2xl">
                <div class="pf-c-card__title">${msg("Tasks")}</div>
                <ak-task-list
                    .relObjAppLabel=${appLabel}
                    .relObjModel=${modelName}
                    .relObjId="${this.provider.pk}"
                ></ak-task-list>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ssf-view": SSFProviderViewPage;
    }
}
