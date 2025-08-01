import "#admin/crypto/CertificateGenerateForm";
import "#admin/crypto/CertificateKeyPairForm";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import {
    CertificateKeyPair,
    CryptoApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-crypto-certificate-list")
export class CertificateKeyPairListPage extends TablePage<CertificateKeyPair> {
    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Certificate-Key Pairs");
    }
    pageDescription(): string {
        return msg(
            "Import certificates of external providers or create certificates to sign requests with.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-key";
    }

    @property()
    order = "name";

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    async apiEndpoint(): Promise<PaginatedResponse<CertificateKeyPair>> {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList(
            await this.defaultEndpointConfig(),
        );
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Private key available?")),
            new TableColumn(msg("Expiry date")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Certificate-Key Pair(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: CertificateKeyPair) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Expiry"), value: item.certExpiry?.toLocaleString() },
                ];
            }}
            .usedBy=${(item: CertificateKeyPair) => {
                return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsUsedByList({
                    kpUuid: item.pk,
                });
            }}
            .delete=${(item: CertificateKeyPair) => {
                return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsDestroy({
                    kpUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: CertificateKeyPair): TemplateResult[] {
        let managedSubText = msg("Managed by authentik");
        if (item.managed && item.managed.startsWith("goauthentik.io/crypto/discovered")) {
            managedSubText = msg("Managed by authentik (Discovered)");
        }
        let color = PFColor.Green;
        if (item.certExpiry) {
            const now = new Date();
            const inAMonth = new Date();
            inAMonth.setDate(inAMonth.getDate() + 30);
            if (item.certExpiry <= inAMonth) {
                color = PFColor.Orange;
            }
            if (item.certExpiry <= now) {
                color = PFColor.Red;
            }
        }
        return [
            html`<div>${item.name}</div>
                ${item.managed ? html`<small>${managedSubText}</small>` : html``}`,
            html`<ak-status-label
                type="info"
                ?good=${item.privateKeyAvailable}
                good-label=${msg(str`Yes (${item.privateKeyType?.toUpperCase()})`)}
            >
            </ak-status-label>`,
            html`<ak-label color=${color}> ${item.certExpiry?.toLocaleString()} </ak-label>`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Certificate-Key Pair")} </span>
                    <ak-crypto-certificate-form slot="form" .instancePk=${item.pk}>
                    </ak-crypto-certificate-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikCryptoCertificatekeypair}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderExpanded(item: CertificateKeyPair): TemplateResult {
        return html`<td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Certificate Fingerprint (SHA1)")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.fingerprintSha1}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Certificate Fingerprint (SHA256)")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.fingerprintSha256}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Certificate Subject")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">${item.certSubject}</div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${msg("Download")}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <a
                                        class="pf-c-button pf-m-secondary"
                                        target="_blank"
                                        href=${item.certificateDownloadUrl}
                                    >
                                        ${msg("Download Certificate")}
                                    </a>
                                    ${item.privateKeyAvailable
                                        ? html`<a
                                              class="pf-c-button pf-m-secondary"
                                              target="_blank"
                                              href=${item.privateKeyDownloadUrl}
                                          >
                                              ${msg("Download Private key")}
                                          </a>`
                                        : html``}
                                </div>
                            </dd>
                        </div>
                    </dl>
                </div>
            </td>
            <td></td>
            <td></td>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Import")} </span>
                <span slot="header"> ${msg("Import Existing Certificate-Key Pair")} </span>
                <ak-crypto-certificate-form slot="form"> </ak-crypto-certificate-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Import")}</button>
            </ak-forms-modal>
            <ak-forms-modal>
                <span slot="submit"> ${msg("Generate")} </span>
                <span slot="header"> ${msg("Generate New Certificate-Key Pair")} </span>
                <ak-crypto-certificate-generate-form slot="form">
                </ak-crypto-certificate-generate-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Generate")}
                </button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-certificate-list": CertificateKeyPairListPage;
    }
}
