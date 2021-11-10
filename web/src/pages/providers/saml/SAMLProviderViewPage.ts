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
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

import { ProvidersApi, SAMLProvider } from "@goauthentik/api";

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
            PFFlex,
            PFDisplay,
            PFGallery,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFSizing,
            PFBanner,
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

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` ${this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by an Application.`}
                  </div>`}<ak-tabs>
                <section
                    slot="page-overview"
                    data-tab-title="${t`Overview`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <dl class="pf-c-description-list pf-m-3-col-on-lg">
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Name`}</span
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
                                                <span class="pf-c-description-list__text"
                                                    >${t`ACS URL`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.acsUrl}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Audience`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.audience || "-"}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Issuer`}</span
                                                >
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
                                        <ak-provider-saml-form
                                            slot="form"
                                            .instancePk=${this.provider.pk || 0}
                                        >
                                        </ak-provider-saml-form>
                                        <button slot="trigger" class="pf-c-button pf-m-primary">
                                            ${t`Edit`}
                                        </button>
                                    </ak-forms-modal>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-changelog"
                    data-tab-title="${t`Changelog`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.provider.pk || ""}
                                targetModelApp="authentik_providers_saml"
                                targetModelName="samlprovider"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
                ${this.provider.assignedApplicationName
                    ? html` <section
                          slot="page-metadata"
                          data-tab-title="${t`Metadata`}"
                          class="pf-c-page__main-section pf-m-no-padding-mobile"
                      >
                          <div class="pf-u-display-flex pf-u-justify-content-center">
                              <div class="pf-u-w-75">
                                  <div class="pf-c-card">
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
                                  </div>
                              </div>
                          </div>
                      </section>`
                    : html``}
            </ak-tabs>`;
    }
}
