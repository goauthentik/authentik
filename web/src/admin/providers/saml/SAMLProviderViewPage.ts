import "#admin/providers/RelatedApplicationButton";
import "#admin/providers/saml/SAMLProviderForm";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/EmptyState";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { MessageLevel } from "#common/messages";

import { AKElement } from "#elements/Base";
import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import {
    CertificateKeyPair,
    CoreApi,
    CoreUsersListRequest,
    CryptoApi,
    ProvidersApi,
    RbacPermissionsAssignedByRolesListModelEnum,
    SAMLMetadata,
    SAMLProvider,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
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

export interface SAMLPreviewAttribute {
    attributes: {
        Name: string;
        Value: string[];
    }[];
    nameID: string;
}

@customElement("ak-provider-saml-view")
export class SAMLProviderViewPage extends AKElement {
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: SAMLProvider;

    @state()
    preview?: SAMLPreviewAttribute;

    @state()
    metadata?: SAMLMetadata;

    @state()
    signer: CertificateKeyPair | null = null;

    @state()
    verifier: CertificateKeyPair | null = null;

    @state()
    previewUser?: User;

    static styles: CSSResult[] = [
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

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.fetchProvider(this.provider.pk);
        });
    }

    fetchPreview(): void {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersSamlPreviewUserRetrieve({
                id: this.provider?.pk || 0,
                forUser: this.previewUser?.pk,
            })
            .then((preview) => {
                this.preview = preview.preview as SAMLPreviewAttribute;
            });
    }

    fetchCertificate(kpUuid: string) {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsRetrieve({ kpUuid });
    }

    fetchSigningCertificate(kpUuid: string) {
        this.fetchCertificate(kpUuid).then((kp) => {
            this.signer = kp;
            this.requestUpdate("signer");
        });
    }

    fetchVerificationCertificate(kpUuid: string) {
        this.fetchCertificate(kpUuid).then((kp) => {
            this.verifier = kp;
            this.requestUpdate("verifier");
        });
    }

    fetchProvider(id: number) {
        new ProvidersApi(DEFAULT_CONFIG).providersSamlRetrieve({ id }).then((prov) => {
            this.provider = prov;
            // Clear existing signing certificate if the provider has none
            if (!this.provider.signingKp) {
                this.signer = null;
            } else {
                this.fetchSigningCertificate(this.provider.signingKp);
            }
            // Clear existing verification certificate if the provider has none
            if (!this.provider.verificationKp) {
                this.verifier = null;
            } else {
                this.fetchVerificationCertificate(this.provider.verificationKp);
            }
        });
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("providerID") && this.providerID) {
            this.fetchProvider(this.providerID);
        }
    }

    renderRelatedObjects(): TemplateResult {
        const relatedObjects = [];
        if (this.provider?.assignedApplicationName) {
            relatedObjects.push(
                html`<div class="pf-c-description-list__group">
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
                </div>`,
            );
        }
        if (this.signer) {
            relatedObjects.push(
                html`<div class="pf-c-description-list__group">
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
                </div>`,
            );
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
                ${this.renderTabMetadata()}
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-preview"
                    id="page-preview"
                    aria-label="${msg("Preview")}"
                    @activate=${() => {
                        this.fetchPreview();
                    }}
                >
                    ${this.renderTabPreview()}
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
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikProvidersSamlSamlprovider}
                    objectPk=${this.provider.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    renderTabOverview(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        return html`${
            this.provider?.assignedApplicationName
                ? nothing
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
                            <span slot="submit">${msg("Update")}</span>
                            <span slot="header">${msg("Update SAML Provider")}</span>
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
                                              value="${ifDefined(this.provider?.urlIssuer)}"
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
                        : nothing
                }
            </div>
        </div>`;
    }

    renderTabMetadata(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        return html`
            ${this.provider.assignedApplicationName
                ? html` <div
                      role="tabpanel"
                      tabindex="0"
                      slot="page-metadata"
                      id="page-metadata"
                      aria-label="${msg("Metadata")}"
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
                                      readonly
                                      value="${ifDefined(this.metadata?.metadata)}"
                                  ></ak-codemirror>
                              </div>
                          </div>
                      </div>
                  </div>`
                : nothing}
        `;
    }

    renderTabPreview(): SlottedTemplateResult {
        if (!this.preview) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        return html` <div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-c-card">
                <div class="pf-c-card__title">${msg("Example SAML attributes")}</div>
                <div class="pf-c-card__body">
                    ${renderDescriptionList([
                        [
                            msg("Preview for user"),
                            html`
                                <ak-search-select
                                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                                        const args: CoreUsersListRequest = {
                                            ordering: "username",
                                        };
                                        if (query !== undefined) {
                                            args.search = query;
                                        }
                                        const users = await new CoreApi(
                                            DEFAULT_CONFIG,
                                        ).coreUsersList(args);
                                        return users.results;
                                    }}
                                    .renderElement=${(user: User): string => {
                                        return user.username;
                                    }}
                                    .renderDescription=${(user: User): TemplateResult => {
                                        return html`${user.name}`;
                                    }}
                                    .value=${(user: User | undefined): number | undefined => {
                                        return user?.pk;
                                    }}
                                    .selected=${(user: User): boolean => {
                                        return user.pk === this.previewUser?.pk;
                                    }}
                                    blankable
                                    @ak-change=${(ev: CustomEvent) => {
                                        this.previewUser = ev.detail.value;
                                        this.fetchPreview();
                                    }}
                                >
                                </ak-search-select>
                            `,
                        ],
                    ])}
                </div>
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-view": SAMLProviderViewPage;
    }
}
