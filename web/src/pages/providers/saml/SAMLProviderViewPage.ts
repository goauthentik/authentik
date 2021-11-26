import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "../../../authentik.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CryptoApi, ProvidersApi, SAMLProvider } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { EVENT_REFRESH } from "../../../constants";
import "../../../elements/CodeMirror";
import "../../../elements/Tabs";
import "../../../elements/buttons/ActionButton";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/events/ObjectChangelog";
import "../RelatedApplicationButton";
import "./SAMLProviderForm";

@customElement("ak-provider-saml-view")
export class SAMLProviderViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersSamlRetrieve({
                id: value,
            })
            .then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: SAMLProvider;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFButton,
            PFBanner,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFGrid,
            AKGlobal,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    renderSigningCert(): Promise<TemplateResult> {
        if (!this.provider?.signingKp) {
            return Promise.resolve(html``);
        }
        return new CryptoApi(DEFAULT_CONFIG)
            .cryptoCertificatekeypairsRetrieve({
                kpUuid: this.provider.signingKp,
            })
            .then((kp) => {
                return html` <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text"
                            >${t`Download signing certificate`}</span
                        >
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <a class="pf-c-button pf-m-primary" href=${kp.certificateDownloadUrl}
                                >${t`Download`}</a
                            >
                        </div>
                    </dd>
                </div>`;
            });
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`${
            this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by an Application.`}
                  </div>`
        }
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-3-col-on-lg">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${t`Name`}</span>
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
                                        >${t`Assigned to application`}</span
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
                                    <span class="pf-c-description-list__text">${t`ACS URL`}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.acsUrl}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${t`Audience`}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.audience || "-"}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${t`Issuer`}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.issuer}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit"> ${t`Update`} </span>
                            <span slot="header"> ${t`Update SAML Provider`} </span>
                            <ak-provider-saml-form slot="form" .instancePk=${this.provider.pk || 0}>
                            </ak-provider-saml-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${t`Edit`}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">
                        ${t`Related objects`}
                    </div>
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-2-col">
                            ${until(this.renderSigningCert())}
                        </dl>
                    </div>
                </div>
                ${
                    this.provider.assignedApplicationName
                        ? html`<div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__title">${t`SAML Metadata`}</div>
                              <div class="pf-c-card__body">
                                  ${until(
                                      new ProvidersApi(DEFAULT_CONFIG)
                                          .providersSamlMetadataRetrieve({
                                              id: this.provider.pk || 0,
                                          })
                                          .then((m) => {
                                              return html`<ak-codemirror
                                                  mode="xml"
                                                  ?readOnly=${true}
                                                  value="${ifDefined(m.metadata)}"
                                              ></ak-codemirror>`;
                                          }),
                                  )}
                              </div>
                              <div class="pf-c-card__footer">
                                  <a
                                      class="pf-c-button pf-m-primary"
                                      target="_blank"
                                      href=${this.provider.metadataDownloadUrl}
                                  >
                                      ${t`Download`}
                                  </a>
                                  <ak-action-button
                                      .apiRequest=${() => {
                                          const fullUrl =
                                              window.location.origin +
                                              this.provider?.metadataDownloadUrl;
                                          return navigator.clipboard.writeText(fullUrl);
                                      }}
                                  >
                                      ${t`Copy download URL`}
                                  </ak-action-button>
                              </div>
                          </div>`
                        : html``
                }
            </div>
        </div>`;
    }
}
