import "@goauthentik/admin/providers/scim/SCIMProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import MDSCIMProvider from "@goauthentik/docs/providers/scim/index.md";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/ModalButton";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
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

import { ProvidersApi, SCIMProvider, Task } from "@goauthentik/api";

@customElement("ak-provider-scim-view")
export class SCIMProviderViewPage extends AKElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersScimRetrieve({
                id: value,
            })
            .then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: SCIMProvider;

    @state()
    syncState?: Task;

    static get styles(): CSSResult[] {
        return [
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
        return html` <ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                @activate=${() => {
                    new ProvidersApi(DEFAULT_CONFIG)
                        .providersScimSyncStatusRetrieve({
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
        </ak-tabs>`;
    }

    renderTabOverview(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` ${!this.provider?.assignedBackchannelApplicationName
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: Provider is not assigned to an application as backchannel provider.",
                      )}
                  </div>`
                : html``}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-l-grid__item pf-m-7-col pf-l-stack pf-m-gutter">
                    <div class="pf-c-card pf-m-12-col pf-l-stack__item">
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
                                            >${msg("URL")}</span
                                        >
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
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-l-stack__item">
                        <div class="pf-c-card__title">
                            <p>${msg("Sync status")}</p>
                        </div>
                        <div class="pf-c-card__body">
                            ${this.syncState
                                ? html` <ul class="pf-c-list">
                                      ${this.syncState.messages.map((m) => {
                                          return html`<li>${m}</li>`;
                                      })}
                                  </ul>`
                                : html` ${msg("Sync not run yet.")} `}
                        </div>

                        <div class="pf-c-card__footer">
                            <ak-action-button
                                class="pf-m-secondary"
                                .apiRequest=${() => {
                                    return new ProvidersApi(DEFAULT_CONFIG)
                                        .providersScimPartialUpdate({
                                            id: this.provider?.pk || 0,
                                            patchedSCIMProviderRequest: this.provider,
                                        })
                                        .then(() => {
                                            this.dispatchEvent(
                                                new CustomEvent(EVENT_REFRESH, {
                                                    bubbles: true,
                                                    composed: true,
                                                }),
                                            );
                                        });
                                }}
                            >
                                ${msg("Run sync again")}
                            </ak-action-button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-5-col">
                    <div class="pf-c-card__body">
                        <ak-markdown .md=${MDSCIMProvider}></ak-markdown>
                    </div>
                </div>
            </div>`;
    }
}
