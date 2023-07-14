import "@goauthentik/admin/providers/RelatedApplicationButton";
import "@goauthentik/admin/providers/saml/SAMLProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/ObjectChangelog";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
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

import {
    CertificateKeyPair,
    CryptoApi,
    ProvidersApi,
    SAMLMetadata,
    SAMLProvider,
} from "@goauthentik/api";

interface SAMLPreviewAttribute {
    attributes: {
        Name: string;
        Value: string[];
    }[];
    nameID: string;
}

@customElement("ak-provider-saml-view")
export class SAMLProviderViewPage extends AKElement {
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
            .then((prov) => {
                this.provider = prov;
                if (prov.signingKp) {
                    new CryptoApi(DEFAULT_CONFIG)
                        .cryptoCertificatekeypairsRetrieve({
                            kpUuid: prov.signingKp,
                        })
                        .then((kp) => (this.signer = kp));
                }
                if (prov.verificationKp) {
                    new CryptoApi(DEFAULT_CONFIG)
                        .cryptoCertificatekeypairsRetrieve({
                            kpUuid: prov.verificationKp,
                        })
                        .then((kp) => (this.verifier = kp));
                }
            });
    }

    @property({ attribute: false })
    provider?: SAMLProvider;

    @state()
    preview?: SAMLPreviewAttribute;

    @state()
    metadata?: SAMLMetadata;

    @state()
    signer?: CertificateKeyPair;

    @state()
    verifier?: CertificateKeyPair;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFGrid,
            PFContent,
            PFCard,
            PFList,
            PFDescriptionList,
            PFForm,
            PFFormControl,
            PFBanner,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    renderRelatedObjects(): TemplateResult {
        const relatedObjects = [];
        if (this.provider?.assignedApplicationName) {
            relatedObjects.push(html`<div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Metadata")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <a
                            class="pf-c-button pf-m-primary"
                            target="_blank"
                            href=${ifDefined(this.provider?.urlDownloadMetadata)}
                        >
                            ${msg("Download")}
                        </a>
                        <ak-action-button
                            class="pf-m-secondary"
                            .apiRequest=${() => {
                                if (!navigator.clipboard) {
                                    return Promise.resolve(
                                        showMessage({
                                            level: MessageLevel.info,
                                            message: this.provider?.urlDownloadMetadata || "",
                                        }),
                                    );
                                }
                                return navigator.clipboard.writeText(
                                    this.provider?.urlDownloadMetadata || "",
                                );
                            }}
                        >
                            ${msg("Copy download URL")}
                        </ak-action-button>
                    </div>
                </dd>
            </div>`);
        }
        if (this.signer) {
            relatedObjects.push(html`<div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text"
                        >${msg("Download signing certificate")}</span
                    >
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <a
                            class="pf-c-button pf-m-primary"
                            href=${this.signer.certificateDownloadUrl}
                            >${msg("Download")}</a
                        >
                    </div>
                </dd>
            </div>`);
        }
        return html` <div class="pf-c-card pf-l-grid__item pf-m-12-col">
            <div class="pf-c-card__title">${msg("Related objects")}</div>
            <div class="pf-c-card__body">
                <dl class="pf-c-description-list pf-m-2-col">
                    ${relatedObjects.length > 0 ? relatedObjects : html`-`}
                </dl>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` <ak-tabs>
            <section slot="page-overview" data-tab-title="${msg("Overview")}">
                ${this.renderTabOverview()}
            </section>
            ${this.renderTabMetadata()}
            <section
                slot="page-preview"
                data-tab-title="${msg("Preview")}"
                @activate=${() => {
                    new ProvidersApi(DEFAULT_CONFIG)
                        .providersSamlPreviewUserRetrieve({
                            id: this.provider?.pk || 0,
                        })
                        .then((preview) => {
                            this.preview = preview.preview as SAMLPreviewAttribute;
                        });
                }}
            >
                ${this.renderTabPreview()}
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
        return html`${
            this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by an Application.")}
                  </div>`
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
                                    <span class="pf-c-description-list__text">${msg(
                                        "ACS URL",
                                    )}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.acsUrl}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg(
                                        "Audience",
                                    )}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.audience || "-"}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg(
                                        "Issuer",
                                    )}</span>
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
                            <span slot="submit"> ${msg("Update")} </span>
                            <span slot="header"> ${msg("Update SAML Provider")} </span>
                            <ak-provider-saml-form slot="form" .instancePk=${this.provider.pk || 0}>
                            </ak-provider-saml-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
                ${this.renderRelatedObjects()}
                ${
                    this.provider.assignedApplicationName
                        ? html` <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__title">${msg("SAML Configuration")}</div>
                              <div class="pf-c-card__body">
                                  <form class="pf-c-form">
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >${msg("EntityID/Issuer")}</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${ifDefined(this.provider?.issuer)}"
                                          />
                                      </div>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >${msg("SSO URL (Post)")}</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${ifDefined(this.provider.urlSsoPost)}"
                                          />
                                      </div>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >${msg("SSO URL (Redirect)")}</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${ifDefined(this.provider.urlSsoRedirect)}"
                                          />
                                      </div>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >${msg("SSO URL (IdP-initiated Login)")}</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${ifDefined(this.provider.urlSsoInit)}"
                                          />
                                      </div>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >${msg("SLO URL (Post)")}</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${ifDefined(this.provider.urlSloPost)}"
                                          />
                                      </div>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >${msg("SLO URL (Redirect)")}</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${ifDefined(this.provider.urlSloRedirect)}"
                                          />
                                      </div>
                                  </form>
                              </div>
                          </div>`
                        : html``
                }
            </div>
        </div>`;
    }

    renderTabMetadata(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`
            ${this.provider.assignedApplicationName
                ? html` <section
                      slot="page-metadata"
                      data-tab-title="${msg("Metadata")}"
                      @activate=${() => {
                          new ProvidersApi(DEFAULT_CONFIG)
                              .providersSamlMetadataRetrieve({
                                  id: this.provider?.pk || 0,
                              })
                              .then((metadata) => (this.metadata = metadata));
                      }}
                  >
                      <div
                          class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
                      >
                          <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__title">${msg("SAML Metadata")}</div>
                              <div class="pf-c-card__body">
                                  <a
                                      class="pf-c-button pf-m-primary"
                                      target="_blank"
                                      href=${this.provider.urlDownloadMetadata}
                                  >
                                      ${msg("Download")}
                                  </a>
                                  <ak-action-button
                                      class="pf-m-secondary"
                                      .apiRequest=${() => {
                                          if (!navigator.clipboard) {
                                              return Promise.resolve(
                                                  showMessage({
                                                      level: MessageLevel.info,
                                                      message:
                                                          this.provider?.urlDownloadMetadata || "",
                                                  }),
                                              );
                                          }
                                          return navigator.clipboard.writeText(
                                              this.provider?.urlDownloadMetadata || "",
                                          );
                                      }}
                                  >
                                      ${msg("Copy download URL")}
                                  </ak-action-button>
                              </div>
                              <div class="pf-c-card__footer">
                                  <ak-codemirror
                                      mode="xml"
                                      ?readOnly=${true}
                                      value="${ifDefined(this.metadata?.metadata)}"
                                  ></ak-codemirror>
                              </div>
                          </div>
                      </div>
                  </section>`
                : html``}
        `;
    }

    renderTabPreview(): TemplateResult {
        if (!this.preview) {
            return html`<ak-empty-state ?loading=${true}></ak-empty-state>`;
        }
        return html` <div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-c-card">
                <div class="pf-c-card__title">${msg("Example SAML attributes")}</div>
                <div class="pf-c-card__body">
                    <dl class="pf-c-description-list pf-m-2-col-on-lg">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("NameID attribute")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${this.preview?.nameID}
                                </div>
                            </dd>
                        </div>
                    </dl>
                </div>
                <div class="pf-c-card__body">
                    <dl class="pf-c-description-list pf-m-2-col-on-lg">
                        ${this.preview?.attributes.map((attr) => {
                            return html` <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${attr.Name}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ul class="pf-c-list">
                                            ${attr.Value.map((value) => {
                                                return html` <li><pre>${value}</pre></li> `;
                                            })}
                                        </ul>
                                    </div>
                                </dd>
                            </div>`;
                        })}
                    </dl>
                </div>
            </div>
        </div>`;
    }
}
